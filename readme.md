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

# 输出格式

```plaintext
# 使用 SRV 记录查询，-t 200 表示超时时间，-c 15 表示 ping 次数，-i 100 表示 ping 间隔时间
> python3 ping.py -srv mc.myserver.com -t 200 -c 15 -i 100
MCPING mc.myserver.com -> host.myserver.com (123.123.123.123) port 8005
[22:26:00.225] 6/2024 players online, version 1.20.1, latency=136.3ms
[22:26:00.501] 6/2024 players online, version 1.20.1, latency=170.4ms
[22:26:00.817] Request timed out
[22:26:01.095] 6/2024 players online, version 1.20.1, latency=177.2ms
[22:26:01.411] Request timed out
[22:26:01.728] Request timed out
[22:26:01.956] 6/2024 players online, version 1.20.1, latency=122.3ms
[22:26:02.271] Request timed out
[22:26:02.546] 6/2024 players online, version 1.20.1, latency=170.4ms
[22:26:02.861] Request timed out
[22:26:03.110] 6/2024 players online, version 1.20.1, latency=143.3ms
[22:26:03.407] 6/2024 players online, version 1.20.1, latency=191.5ms
[22:26:03.669] 6/2024 players online, version 1.20.1, latency=157.2ms
[22:26:03.888] 6/2024 players online, version 1.20.1, latency=117.6ms
[22:26:04.204] Request timed out

--- mc.myserver.com mcping statistics ---
15 packets transmitted, 9 received, 40.0% packet loss, time 4116ms
rtt min/avg/max/mdev = 117.580/154.033/191.534/25.616 ms
```