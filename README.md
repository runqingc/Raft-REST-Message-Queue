



run test

```sh
cd test 
python3 -m pytest message_queue_test.py 
python3 -m pytest election_test.py  
```



run a single node:
```sh
python3 src/node.py config.json 0
```




你可以想一些test case放在这里

Test case:

所有的日志目前发的都是空，还没implement

没收到heart beat，需要一直发

client request to follower, reply failure



假设这里的get_topic 会返回所有的topic而不删除topic
get_message则会把message删除
在老师的测试用例里貌似没有测连续对一个topic进行两次get 操作的情况