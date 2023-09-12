# SimpleDns
简单的自定义dns服务器，将某些域名定向解析到固定ip地址

执行`vim /etc/systemd/system/simpleDns.service`  
编辑内容如下
```bash
[Unit]
Description=simple dns service
After=syslog.target network.target
Wants=network.target


[Service]
Type=simple
User=root
WorkingDirectory=/home/nano/Project/SimpleDns
ExecStart=/usr/bin/python3 main.py
Restart= always
RestartSec=1min

[Install]
WantedBy=multi-user.target
```
开启自启动
```bash
#启动natServer
systemctl daemon-reload
systemctl start natServer
#设置为开机启动
systemctl enable natServer
```
