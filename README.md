# socialModules
Several modules to write and read in several social netwoks and content sites.

We have two modules to manage content:
* Content (Reading/Writing content)
* Queing (Storing and managing temporal storage of content).

And two modules to manage the way queues are stored:
* Caching (local storage)
* Buffering (using the Buffer API, **abandoned**).

The previous home of this code was [https://github.com/fernand0/scripts](https://github.com/fernand0/) and it has been moved here follogin [Splitting a subfolder out into a new repository](https://docs.github.com/en/github/using-git/splitting-a-subfolder-out-into-a-new-repository)

We can manage content from several sources, using a common interface, such as [Twitter](https://github.com/fernand0/socialModules/blob/master/moduleTwitter.py), [Telegram](https://github.com/fernand0/socialModules/blob/master/moduleTelegram.py), ...
Each one has its own specific ways of initialization for the corresponding API.
