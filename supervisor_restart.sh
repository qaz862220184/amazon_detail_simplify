
# 判断scrapy进程存不存在，存在则不进行操作
if pgrep -x "scrapyd" > /dev/null
then
    echo "scrapyd 进程已存在"
else
    supervisorctl restart commodity_simplify_rankings
fi

sleep 5
supervisorctl restart commodity_simplify_client
echo "success"
