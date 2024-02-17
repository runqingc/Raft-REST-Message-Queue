



run test

```sh
cd test 
python3 -m pytest message_queue_test.py 
```



run node:

```sh
python3 src/node.py config.json 0
```





Test case:

没收到heart beat，一直发

client request to follower, reply failure