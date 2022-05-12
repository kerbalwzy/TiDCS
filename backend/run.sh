#!/bin/bash
if [ "$1" == "stop" ]; then
    echo '关闭进程'
    fuser -k -n tcp 43998
elif [ "$1" == "start" ]; then
    fuser -k -n tcp 43998
    source "/root/.virtualenvs/TiDCS/bin/activate"
    echo '激活虚拟环境'
    cd /root/TiDCS/backend
    echo '启动进程'
    python main.py  > /dev/null 2>&1 &
    export https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890 all_proxy=socks5://127.0.0.1:7890
else
    echo 'Usage: bash run.sh [start, stop]'
fi