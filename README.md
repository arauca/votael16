# votael16
Dónde votar en la Consulta Popular este 16 de junio de 2017.

## How to build the index
- Install Composer
```
php -r "copy('https://getcomposer.org/installer', 'composer-setup.php');"
php -r "if (hash_file('SHA384', 'composer-setup.php') === '669656bab3166a7aff8a7506b8cb2d1c292f042046c5a994c43155c0be6190fa0355160742ab2e1c88d40d5be660b410') { echo 'Installer verified'; } else { echo 'Installer corrupt'; unlink('composer-setup.php'); } echo PHP_EOL;"
php composer-setup.php
php -r "unlink('composer-setup.php');"
```
- Run `php composer.phar install`
- Run `vendor/bin/jsindex data/` to build the index to `jssearch.index.js` (PHP >= 5.4.0 required)

## Current issues
I think we need a separate .html file for every voting center. The index is generated correctly, but the responses to the queries are currently useless. Run `vendor/bin/jsindex tests/data/` to see a different example, and see the [original demo](http://cebe.github.io/js-search/#demo) for more inspiration.
