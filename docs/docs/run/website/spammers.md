It is necessary to monitor forum activity and ban spammer accounts in order to
keep the forum usable for everyone.

Spammers register in order to promote links to products or services on the
[forum](https://forum.jammr.net/). Spam posts may be new forum topics or
replies to existing topics. When deciding whether a post is spam, look for
links. Links may be hidden in punctuation or in a quoted reply.

To ban a spammer:

1. Log in to the server: `ssh node1.jammr.net`
1. Run the banspammer command with the spammer's username: `docker exec -it website ./manage-website.py banspammers --username <username>`
