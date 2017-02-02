# -*- mode: ruby -*-
# vi: set ft=ruby :

## Vagrant :: Ubuntu PostgreSQL :: Vagrant File ##

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
#  pass in 2 for the vagrant api version

Vagrant.configure('2') do |config| 

  config.vm.box = 'ubuntu/trusty64'

  # VM config
  config.vm.define :psql_node do |psql_node|
    psql_node.vm.network :private_network, ip: '192.168.2.12'
    psql_node.vm.network :forwarded_port, host: 5432, guest: 5432
    psql_node.vm.network :forwarded_port, host: 5433, guest: 5433

    psql_node.vm.hostname = "postgres-ss"

    psql_node.vm.provider 'virtualbox' do |v|
      v.customize ['modifyvm', :id, '--name', 'ubuntu-postgres']
      v.customize ['modifyvm', :id, '--cpus', '1']
      v.customize ['modifyvm', :id, '--memory', 2048]
      v.customize ['modifyvm', :id, '--ioapic', 'off']
      v.customize ['modifyvm', :id, '--natdnshostresolver1', 'on']
    end

    # Update package list
    psql_node.vm.provision :shell, :inline => 'sudo apt-get update'
  end
end
