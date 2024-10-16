# https://phoenixnap.com/kb/install-spark-on-ubuntu
sudo apt install default-jdk scala git -y
java -version; javac -version; scala -version; git --version
wget https://dlcdn.apache.org/spark/spark-3.5.3/spark-3.5.3-bin-hadoop3.tgz
wget https://downloads.apache.org/spark/spark-3.5.3/spark-3.5.3-bin-hadoop3.tgz.sha512
shasum -a 512 -c spark-3.5.3-bin-hadoop3.tgz.sha512
tar xvf spark-*.tgz
sudo mv spark-3.5.3-bin-hadoop3 /opt/spark
/opt/spark/bin/spark-shell --version
echo "export SPARK_HOME=/opt/spark" >> ~/.bashrc
echo "export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin" >> ~/.bashrc
echo "export PYSPARK_PYTHON=/usr/bin/python3" >> ~/.bashrc
source ~/.bashrc
