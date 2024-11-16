# BoB event plugins

Functionality can be extended here, by running any executable of your choice before or after certain events are processed by bob.

## Use

Just place a script etc. in to the relevant directoty - they are organisaed as <object> / <action>

For example, if you want your own actions to happen after a host is added, simple put your script into _./host/post-add/my-new-script.sh_

and make sure it is marked as execuatble.
