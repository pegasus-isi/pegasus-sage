This is a special use case for Sage. This directory contains a recipe for building an example Sage app with Pegasus and HTCONDOR ready to be deployed on Sage's Waggle nodes (IoT nodes). The workflow runs entirely on a single Waggle node and pushes data to the Beehive datastore.

## Getting started

* Login to the [SAGE Portal](https://portal.sagecontinuum.org) . 
* If is your first time logging in, then navigate to your account profile  [SAGE Account Profile](https://portal.sagecontinuum.org/account/profile) .
* Request developer acccess to the waggle nodes. When you click on [My Nodes Tabbed Menu](https://portal.sagecontinuum.org/account/nodes) you will see the support email address to contact.
* Once your access is enabled, you need to enable your access to the waggle nodes by setting up your ssh keys. Follow the instructions given [here](https://portal.sagecontinuum.org/account/access).

## Commands to run on sage

Login to one of the waggle nodes that you have access for. You can easily check that in your [My Nodes Tabbed Menu](https://portal.sagecontinuum.org/account/nodes).

Once on the node checkout this github repository

```
git clone https://github.com/pegasus-isi/pegasus-sage.git
```

Change to the workflow-in-a-box directory. 

```
cd pegasus-sage/workflow-in-a-box
```

Build the plugin app

```
sudo pluginctl build .
```

Run the edge app

```
sudo pluginctl run --name workflow-in-a-box 10.31.81.1:5000/local/workflow-in-a-box
```
