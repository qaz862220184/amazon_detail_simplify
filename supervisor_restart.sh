
# 判断是否已存在屏幕，存在就不重启
xorg_tag=$(ps -ef | grep xorg | grep -v "grep" | wc -l)

if [ "$xorg_tag" -eq "0" ]; then
    sleep 60
    # 首先启动一下 xorg
    /usr/lib/xorg/Xorg :10 -auth ~/.Xauthority -config /etc/X11/xrdp/xorg.conf -noreset -nolisten tcp -logfile .xorgxrdp.%s.log &
    sleep 10
    # 接下来启动一下 scrapyd
    supervisorctl restart commodity_rankings

else
    echo "Xorg 已存在，不执行重启操作"
fi

# 判断scrapy进程存不存在，存在则不进行操作
if pgrep -x "scrapyd" > /dev/null
then
    echo "scrapyd 进程已存在"
else
    supervisorctl restart commodity_rankings
fi

sleep 5
supervisorctl restart commodity_client
echo "success"
