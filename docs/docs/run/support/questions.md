Users most often ask for help through the [technical support
forum](https://forum.jammr.net/1/) or the info@jammr.net email address. These
must be monitored regularly in order to respond promptly.

Common user questions are covered by the sticky posts in the technical support
forum. Often it is enough to point the user at the audio setup guide, user
interface overview, or how to jam together successfully post.

To ease forum activity monitoring, there is a script in
`webapp/forum/email_notifications/management/commands/email_notifications.py`
that sends email notifications. It runs automatically as the
`send_forum_notifications` container on the server.
