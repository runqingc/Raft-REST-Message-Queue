# **Raft**

![image-20240212103818823](/Users/cairunqing/Library/Application Support/typora-user-images/image-20240212103818823.png)

![image-20240212103946792](/Users/cairunqing/Library/Application Support/typora-user-images/image-20240212103946792.png)



![image-20240212104113167](/Users/cairunqing/Library/Application Support/typora-user-images/image-20240212104113167.png)

![image-20240212104154567](/Users/cairunqing/Library/Application Support/typora-user-images/image-20240212104154567.png)

![image-20240212104735511](/Users/cairunqing/Library/Application Support/typora-user-images/image-20240212104735511.png)

![image-20240212104629075](/Users/cairunqing/Library/Application Support/typora-user-images/image-20240212104629075.png)

![image-20240212104756729](/Users/cairunqing/Library/Application Support/typora-user-images/image-20240212104756729.png)

![image-20240212163735381](/Users/cairunqing/Library/Application Support/typora-user-images/image-20240212163735381.png)

![image-20240212163909081](/Users/cairunqing/Library/Application Support/typora-user-images/image-20240212163909081.png)

![image-20240212164051565](/Users/cairunqing/Library/Application Support/typora-user-images/image-20240212164051565.png)

![image-20240212165121525](/Users/cairunqing/Library/Application Support/typora-user-images/image-20240212165121525.png)



![image-20240212164836965](/Users/cairunqing/Library/Application Support/typora-user-images/image-20240212164836965.png)

![image-20240212165241109](/Users/cairunqing/Library/Application Support/typora-user-images/image-20240212165241109.png)



![image-20240212165650040](/Users/cairunqing/Library/Application Support/typora-user-images/image-20240212165650040.png)

![image-20240213102617891](/Users/cairunqing/Library/Application Support/typora-user-images/image-20240213102617891.png)





一些问题（假设不出现问题）：

节点1发起vote request，还没有收到所有回复节点2就又发起了一起投票请求



资料

https://github.com/maemual/raft-zh_cn/blob/master/raft-zh_cn.md



一些情况（假设出现问题）：





我们先统一一下用词，提交是指：leader确定某条日制已经被复制到大多数的
