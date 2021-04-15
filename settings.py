import io
import secrets
import yaml


class Settings:
    key = None
    host = None
    port = None
    settings_filename = 'settings.yml'

    def __init__(self):
        print('\nInitializing settings from the %s file' % self.settings_filename)
        # Загружаем конфиг.
        # Используем безопасную загрузку конфига, чтобы там не оказалось ничего исполняемого
        with open(self.settings_filename, 'r') as ymlfile:
            try:
                cfg = yaml.safe_load(ymlfile)
                # print('cfg:', cfg)
            except yaml.YAMLError as exc:
                print(exc)
                exit()

        # for key in cfg:
        #     value = cfg[key]
        #     print('# key:', key, ', # value:',value)
        settings_need_save = False
        # Если в кофиге нет массива - инициализируем его
        if not cfg:
            cfg = {}

        if 'key' in cfg and cfg['key']:
            pass
        else:
            print('Ключ не найден. Создаём новый')
            cfg['key'] = secrets.token_hex(16)
            settings_need_save = True

        if 'host' in cfg and cfg['host']:
            pass
        else:
            print('Host не найден. Используем host по умолчанию.')
            cfg['host'] = '127.0.0.1'
            settings_need_save = True

        if 'port' in cfg and cfg['port']:
            pass
        else:
            print('Port не найден. Используем port по умолчанию.')
            cfg['port'] = 5002
            settings_need_save = True

        # Если конфига не нашли - записываем свой
        if settings_need_save:
            print('Сохраняем обновлённые настройки в файл')
            # # Write YAML file
            with io.open(self.settings_filename, 'w', encoding='utf8') as outfile:
                yaml.dump(cfg, outfile, default_flow_style=False, allow_unicode=True)

        # Загружаем все итоговые параметры в память
        self.key = cfg['key']
        self.host = cfg['host']
        self.port = cfg['port']

        # print('Key:', self.key)
        # print('Host:', self.host)
        # print('Port:', self.port)
