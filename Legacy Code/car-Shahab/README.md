## Getting Started
This is a quick guide explaining how to get started contributing to our code base. Before starting make sure have setup git as a command line tool and configured [SSH on your machine](https://docs.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh).

1. Clone the repo onto your machine: `git clone git@github.com:Cardiff-Autonomous-Racing/car.git`
1. Change directories into the folder where you cloned the repository: `cd car`
1. Checkout a branch to make your changes: `git checkout -b working_branch`
1. When your changes are ready stage, commit, push them to the upstream repo:

``` commandline
git add *
git commit -m "Demonstrate how to make a change"
git push origin working_branch
```

Once you've pushed your changes to the upstream repo, raise a pull request to merge the changes from your branch to the main branch.

## Commit Messages

A well-crafted commit message is the best way to communicate context about a change to fellow developers. The commit message should tell other users why a change was made. [This](https://chris.beams.io/posts/git-commit/) guide explains how to write a good commit message.

## Other Useful Commands
To see what changes you've made on your repository run the following command:
`git status`

The following undoes all the changes on your machine:
`git reset --hard`

If you haven't setup SSH, you can configure your git to push changes via HTTPS.
``` commandline
git config --global user.email "youremail@example.com"
git config --global user.name "Name or Student Number"
```
