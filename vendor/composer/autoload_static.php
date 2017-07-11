<?php

// autoload_static.php @generated by Composer

namespace Composer\Autoload;

class ComposerStaticInit31847afe1ab71247322338ca42ac652e
{
    public static $prefixLengthsPsr4 = array (
        'c' => 
        array (
            'cebe\\jssearch\\' => 14,
        ),
    );

    public static $prefixDirsPsr4 = array (
        'cebe\\jssearch\\' => 
        array (
            0 => __DIR__ . '/../..' . '/lib',
            1 => __DIR__ . '/..' . '/cebe/js-search/lib',
        ),
    );

    public static function getInitializer(ClassLoader $loader)
    {
        return \Closure::bind(function () use ($loader) {
            $loader->prefixLengthsPsr4 = ComposerStaticInit31847afe1ab71247322338ca42ac652e::$prefixLengthsPsr4;
            $loader->prefixDirsPsr4 = ComposerStaticInit31847afe1ab71247322338ca42ac652e::$prefixDirsPsr4;

        }, null, ClassLoader::class);
    }
}
