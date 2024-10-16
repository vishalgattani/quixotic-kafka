# Cassandra

- https://archive.apache.org/dist/cassandra/4.0.0/


# Startup

```sh
cd apache-cassandra-4.0.0/ && bin/cassandra #This will run Cassandra as the authenticated Linux user.
```

```sh
tail -f logs/system.log
#Cassandra is ready when you see an entry like this in the system.log:
#INFO  [main] 2019-12-17 03:03:37,526 Server.java:156 - Starting listening for CQL clients on localhost/127.0.0.1:9042 (unencrypted)...
```

Check the status of Cassandra:
```
$ bin/nodetool status
```
The status column in the output should report UN which stands for "Up/Normal".

Alternatively, connect to the database with:
```
$ bin/cqlsh
```
