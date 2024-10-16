sudo apt update -y && sudo apt install openjdk-8-jdk -y
java -version
sudo apt install apt-transport-https -y
sudo apt update -y
echo "deb https://debian.cassandra.apache.org 40x main" | sudo tee -a /etc/apt/sources.list.d/cassandra.sources.list
sudo mkdir -p /etc/apt/keyrings
sudo curl -L https://downloads.apache.org/cassandra/KEYS -o /etc/apt/keyrings/apache-cassandra.asc
sudo apt update -y
sudo apt install cassandra -y
echo "Checking Cassandra installation"
nodetool status
sudo systemctl status cassandra
echo "Backing up Cassandra configuration"
sudo cp /etc/cassandra/cassandra.yaml /etc/cassandra/cassandra.yaml.backup
