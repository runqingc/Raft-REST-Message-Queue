



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