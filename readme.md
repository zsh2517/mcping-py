# mcping.py

使用 [ServerListPing 协议](https://wiki.vg/Server_List_Ping)来对一个 Minecraft 服务器进行 Ping 操作。

由 AI 编写。所有功能尚未完全测试。

**可能需要安装 `dnspython` 包。**

# 使用方法

## SRV 记录查询

```bash
# 假设 _minecraft._tcp.mc.myserver.com 的 SRV 是 5 0 12345 host.myserver.com

python mcping.py -srv mc.myserver.com
```

## 直接指定主机和端口

```bash
python mcping.py -host host.myserver.com:12345
python mcping.py host.myserver.com 12345
python mcping.py host.myserver.com:12345
```

## `-c` 命令

`-c` 命令用于指定发送 ping 的次数。如果未指定 `-c`，程序将无限期地进行 ping 操作。

## `-t` 命令

`-t` 命令用于指定超时时间（以毫秒为单位）。如果未指定 `-t`，则默认超时时间为 1000 毫秒。

超过超时时间后，将会提示 `[22:23:19.221] Request timed out`。

## `-i` 命令

`-i` 命令用于指定 ping 之间的间隔时间（以毫秒为单位）。如果未指定 `-i`，则默认间隔为 1000 毫秒。

在上一次 ping 结束后，会等待指定的时间，然后进行下一次 ping。

