To make translations:

1) symlink templates in tns_glass

2) go find the translations and build the po files
  % python manage.py makemessages --all --symlinks

3) compile them
  % python manage.py compilemessages

Check in the resulting changes and push.
