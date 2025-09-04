+++
date = '2025-08-30'
draft = false
title = '记：沙箱环境变量不生效 Bug 排查'
summary = ' '

+++

## 背景

接到 [blueking-paas](https://github.com/TencentBlueKing/blueking-paas) 沙箱自定义环境变量的需求后，照常先进行需求分析、产品设计，然后编写代码 + 本地 API 测试 + 提 PR，接下来就是愉快的和前端联调了。

之后流水线发布到联调环境，前端通知自测，自己在界面上到处点点点也没发现什么问题（现在看确实缺少一些测试经验 orz）。于是写了份体验文档扔到群里，让其他同事也测试看看，没问题的话就可以发布到预发布环境 & 正式环境，上线这个功能了。

但有同事在沙箱中测试时，发现自己编辑的环境变量并没有生效？这就不太对劲了，为什么环境变量没有生效呢？

## 本地复现 Bug

收到反馈，首先需要在本地把这个 bug 复现出来。具体步骤：创建沙箱 -> 在 SaaS 应用代码中打印环境变量日志 -> 启动 SaaS 应用进程。对于第三步，之前的 deploy 请求是不带环境变量的，但我最新的 deploy API 需要环境变量，而本地没有最新的前端环境，怎么给后端发送带有环境变量的 deploy 请求？

因为是直接改写了原来的 API，将 EnvVars 扔到 channel 中去异步执行启动命令，因此后端的 API 是最新的，我们直接把 **联调环境** 的 deploy API 的 http 请求 copy as fetch，扔到浏览器的 console 中发送请求就好了。

```go
func DeployHandler(s *WebServer, svc service.DeployServiceHandler) gin.HandlerFunc {
	return func(c *gin.Context) {
		envVars := map[string]string{}
		if raw := c.PostForm("env_vars"); raw != "" {
			// env_vars 非空，解析自定义环境变量
			if err := json.Unmarshal([]byte(raw), &envVars); err != nil {
				c.JSON(
					http.StatusBadRequest,
					gin.H{"message": fmt.Sprintf("invalid env_vars format: %s", err.Error())},
				)
				return
			}
		}
        
        // ... 其他处理

		select {
		case s.ch <- devsandbox.AppReloadEvent{
			ID:       status.DeployID,
			Rebuild:  status.StepOpts.Rebuild,
			Relaunch: status.StepOpts.Relaunch,
			EnvVars:  envVars,
		}:
			c.JSON(http.StatusOK, gin.H{"deployID": status.DeployID})
		default:
			c.JSON(
				http.StatusTooManyRequests,
				gin.H{"message": "app is deploying, please wait for a while and try again."},
			)
		}
	}
}
```

再次发送请求，等待应用进程启动后查看沙箱进程日志，发现日志打印出来的环境变量值确实为 None。

奇怪了，本地 postman 测 API 的时候是能够正常拿到环境变量的，为啥这里就没生效？

## 排查过程

[blueking-paas](https://github.com/TencentBlueKing/blueking-paas) 这个项目比较特殊，它的 ApiServer 是一个 Django 项目，提供众多 REST API，沙箱开发功能只是它的一部分。

![image.png](https://s2.loli.net/2025/08/30/zLY2AwOo8GbRTQp.png)

而用户创建沙箱后，ApiServer 会通过 create API 下发 K8s 集群资源，具体来说：新建一个沙箱专属命名空间，在里面创建 configmap、ingress、service 等资源，然后运行一个 pod。

在 pod 中会起沙箱的 gin server，接受前端相关请求，比如 **启动 SaaS 进程、提交代码** 等等。

![7fbb608f3d62baffc2a7ba8840820880_720.png](https://s2.loli.net/2025/08/30/xkd4iAK9ELm1ygr.png)

也就是说，在用户使用沙箱开发时，前端同时与两个后端 server 进行交互：先通过 ApiServer 下发集群资源 -> 沙箱服务启动后，与沙箱的 gin server 交互。

下发集群资源的这个过程，需要拉取镜像仓库的沙箱镜像，所以在本地测试沙箱 server 的新 API 时，先得经过一个打包 + 上传镜像的过程，然后在本地通过 ApiServer 创建沙箱，拉取最新镜像进行测试。

修改 deploy API 并增加调试日志后，按照前面的思路，把联调环境的 deploy 请求 copy as fetch 拿到本地进行测试，发现后端始终拿不到前端请求发来的环境变量（？？？）

同一个后端 API，用 postman 测试能够正常拿，但在 web console 中却拿不到，为啥？

### Bug 1：错误的 Content-Type

换个角度考虑，有没有可能是请求形式的问题？我把 postman 扔到一边，直接使用本地的前端环境发送 deploy 请求，仔细核对了两个请求的请求头和响应体，发现了罪魁祸首：请求头中的 `Content-Type` 。

回顾一下目前的 deploy API：

```go
func DeployHandler(s *WebServer, svc service.DeployServiceHandler) gin.HandlerFunc {
	return func(c *gin.Context) {
		envVars := map[string]string{}
		if raw := c.PostForm("env_vars"); raw != "" {
			// env_vars 非空，解析自定义环境变量
			if err := json.Unmarshal([]byte(raw), &envVars); err != nil {
				c.JSON(
					http.StatusBadRequest,
					gin.H{"message": fmt.Sprintf("invalid env_vars format: %s", err.Error())},
				)
				return
			}
           // ... 其他处理
		}
```

可以看到，当前 DeployHandler 获取 env_vars 是通过 gin context 的 PostForm 方法，而这个方法接收的是前端传到后端的表单数据。

在 [blueking-paas](https://github.com/TencentBlueKing/blueking-paas) 这个项目中，ApiServer 模块提供众多的 API，和前端交互时绝大多数情况都是通过 json 传输，很少会使用表单这种方式，那么自然就会猜测，会不会是这个 PostForm 的问题？

核对了本地环境下 postman 发送请求的 `Content-Type` 和联调环境的 `Content-Type` ，发现前者是 `application/x-www-form-urlencoded`，而后者是 `application/json` 。

参考 PostForm 的源码：

```go
// PostForm 获取表单中指定 key 的值（解析 x-www-form-urlencoded 或 multipart/form-data）
func (c *Context) PostForm(key string) string {
    value, _ := c.GetPostForm(key)
    return value
}

// GetPostForm 获取表单值
func (c *Context) GetPostForm(key string) (string, bool) {
    if c.Request.PostForm == nil {
        c.Request.ParseMultipartForm(c.engine.MaxMultipartMemory)
    }
    if values := c.Request.PostForm[key]; len(values) > 0 {
        return values[0], true
    }
    return "", false
}
```

上面的 `c.Request.PostForm` 是 Go 标准库 net/http 中解析后的表单数据，它只能处理两种 `Content-Type`：`application/x-www-form-urlencoded` 和 `multipart/form-data`。

于是，真正的问题自然就水落石出：在联调环境下，前端发送带有 env_vars 的请求，其 `Content-Type` 是 `application/json`，而后端接受 env_vars 的方法是 PostForm，只能够处理上面提到的两种 `Content-Type`。

当 json 形式的 env_vars 到达后端，并不会在 GetPostForm 中被成功解析，因此直接返回 `"", false` 给 PostForm，所以后端拿到的 env_vars 为空，用户自定义的环境变量就不会被后续的热更新代码注入应用进程。

### Bug 2：supervisor 现存的问题

后端拿到用户自定义的环境变量后，会将其扔到 channel 里去异步调用 Relaunch 方法实现热更新（保证 pod 不重建）。

```go
func DeployHandler(s *WebServer, svc service.DeployServiceHandler) gin.HandlerFunc {
	return func(c *gin.Context) {
        // ... 解析 json 请求体中的环境变量 + 其他处理

		select {
		case s.ch <- devsandbox.AppReloadEvent{
			ID:       status.DeployID,
			Rebuild:  status.StepOpts.Rebuild,
			Relaunch: status.StepOpts.Relaunch,
            // 将 env_vars 扔到 channel 中
			EnvVars:  envVars,
		}:
			c.JSON(http.StatusOK, gin.H{"deployID": status.DeployID})
		default:
			c.JSON(
				http.StatusTooManyRequests,
				gin.H{"message": "app is deploying, please wait for a while and try again."},
			)
		}
	}
}
```

热更新的底层原理，是使用 python 编写的进程管理工具 supervisor 来实现。

supervisor：[Supervisor/supervisor: Supervisor process control system for Unix (supervisord)](https://github.com/Supervisor/supervisor)

具体来说，supervisor 会起一个 **supervisord** 进程对 SaaS 应用进程进行托管（可以理解成 SaaS 应用进程是 supervisord 的子进程），当前端传入环境变量后，supervisord 会重启应用进程，重新读取 supervisord 进程中的新环境变量。

而重启应用进程之前，需要将新环境变量传入 supervisor 的配置文件，才能将其加载到 **supervisord** 进程中。在我们的环境变量中存在若干 URL 路径，可能会包含有 `%` 等字符。

而 supervisor 的配置文件中的环境变量部分，并不允许包含 `%` 和 `"` 这两种字符，需要对其进行转义：

![image.png](https://s2.loli.net/2025/09/02/gh2Evcy38XQCVPW.png)

于是需要修改处理 supervisor 配置文件的代码，在遍历环境变量时对环境变量值进行转义：

```go
// returns a new SupervisorConf
func makeSupervisorConf(processes []base.Process, procEnvs ...appdesc.Env) (*SupervisorConf, error) {
	conf := &SupervisorConf{
		RootDir: supervisorDir,
		Port:    rpcPort,
	}

	if procEnvs != nil {
		//if err := validateEnvironment(procEnvs); err != nil {
		//	return nil, err
		//}
		envs := make([]string, len(procEnvs))
		for i, env := range procEnvs {
			// 仅转义 % 和 "
			escapedValue := escapeForSupervisor(env.Value)
			envs[i] = fmt.Sprintf(`%s="%s"`, env.Name, escapedValue)
		}
		conf.Environment = strings.Join(envs, ",")
	}

	for _, p := range processes {
		conf.Processes = append(conf.Processes, base.ProcessConf{
			Process:     p,
			ProcLogFile: filepath.Join(conf.RootDir, "log", p.ProcType+".log"),
		})
	}
	return conf, nil
}

// escapeForSupervisor 转义值中的特殊字符
func escapeForSupervisor(value string) string {
	escaped := strings.ReplaceAll(value, "%", "%%")
	escaped = strings.ReplaceAll(escaped, `"`, `\"`)
	return escaped
}
```

但在本地测试时又出现了问题（怎么这么多问题 = =）

因为应用进程的环境变量是通过继承 supervisord 进程获取的，根据配置文件的要求，环境变量需要放到 `[supervisord]` 这个 section 中。

```ini
[unix_http_server]
file = /cnb/devsandbox/supervisor/supervisor.sock

[supervisorctl]
serverurl = unix:///cnb/devsandbox/supervisor/supervisor.sock

[supervisord]
pidfile     = /cnb/devsandbox/supervisor/supervisord.pid
logfile     = /cnb/devsandbox/supervisor/log/supervisord.log
interpolate = false
environment = 
SOURCE_FETCH_URL="http://ip:port/default/home/gotest2%%3Adefault%%3Amaster%%3Ac7c75432ebbdd32bd913fe8a05ae36eed9a5666c%%3Adev/tar?AWSAccessKeyId=example&Signature=example%%2FMFI8%%3D&Expires=1756347407",
other environment variables...

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[program:scheduler]
command         = /cnb/process/scheduler
stdout_logfile  = /cnb/devsandbox/supervisor/log/scheduler.log
redirect_stderr = true

[program:web]
command         = /cnb/process/web
stdout_logfile  = /cnb/devsandbox/supervisor/log/web.log
redirect_stderr = true

[inet_http_server]
port = 127.0.0.1:9001
```

可以看到，配置文件（ini 格式）中的符号已经按照官方文档的要求进行了转义，按理来说，是可以正常启动 supervisor server，并实现热更新的，但是测试下来发现 server 并无法正常启动，会报如下错误：

```
Error: Format string 'SOURCE_FETCH_URL="http://ip:port/default/home/gotest2%%3Adefault%%3Amaster%%3Ac7c75432ebbdd32bd913fe8a05ae36eed9a5666c%%3Adev/tar?AWSAccessKeyId=example&Signature=example%%2FMFI8%%3D&Expires=1756347407",
other environment variables...' for 'environment' is badly formatted: unsupported format character 'A' (0x41) at index 3460
```

这表明 `[supervisord]` section 下的环境变量并没有被正确转义！

是否为 section 的原因？于是我把配置文件中的 environment 挪到 `[program:scheduler]` 和 `[program:web]` 中，再次尝试启动，并没有出现上面的 unsupported format 错误。

根据上面的测试与分析，可以确定是 `[supervisord]` 这个 section 中并没有正确地对 `%` 进行转义，**这是 supervisor 现存的一个 BUG**。

把 supervisor 这个项目 clone 到本地，深入阅读它的源码，发现在 `supervisor/options.py:660` 这一行，`%` 被提前转义了：

```python
environ_str = get('environment', '') # 这一行导致了上面的 BUG
environ_str = expand(environ_str, expansions, 'environment')
section.environment = dict_of_key_value_pairs(environ_str)
```

这里的 environment 被提前转义后，会被传到 expand 函数中，而 expand 函数会对其进行二次转义，导致出现上面的 unsupported format。

再讲具体一点，用户在 `[supervisord]` section 下设置了已经正确转义的 environment，然后上面的 `get` 函数先把 environment 中的 `%%` 解析成了 `%`，然后这个 environment 被传到 expand 函数，**此时 expand 预期接受的值应该是 `%%`，但实际上接收到的是 `%` **，之后 expand 会对其做同样的操作，这样就导致了 unsupported format。

如何修复呢？

supervisor 现在的 `get` 函数提供了一个参数 `do_expand`，用来控制是否对指定字符进行转义扩展，而且这个参数默认是 true，我们只需要在 `get` 这一层将 `do_expand` 置为 false 即可。

于是就有了这个 PR：https://github.com/Supervisor/supervisor/pull/1695

这样的话，环境变量就能够被正确加载到配置文件中，进而实现环境变量的热更新了。

