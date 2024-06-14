import requests
import datetime
import json
from pprint import pprint
from config import access_token


class YANDEX:
    def __init__(self, token_ya):
        self.token_ya = token_ya

    def create_folder(self, folder_name):
        url = f'https://cloud-api.yandex.net/v1/disk/resources'
        params = {'path': f'{folder_name}'}
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'OAuth {self.token_ya}'
        }
        response = requests.put(url, headers=headers, params=params)
        return response

    def get_folder_url(self, folder_name, file_name):
        params = {'path': f'{folder_name}/{file_name}', 'overwrite': 'true'}
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'OAuth {self.token_ya}'
        }
        response = requests.get('https://cloud-api.yandex.net/v1/disk/resources/upload', params=params, headers=headers)
        url_for_upload = response.json()['href']
        return url_for_upload

    def put_file_to_folder(self, file_name, folder_name, file_url):
        url_for_upload = self.get_folder_url(folder_name, file_name)
        file_data = requests.get(file_url).content
        response = requests.put(url_for_upload, files={'file': (file_name, file_data)})
        return response


class VK(YANDEX):
    def __init__(self, access_token, version='5.199'):
        self.user_id = input('Введите ваш id "Вконтакте": ')
        if not self.user_id.isdigit():
            raise ValueError('ID должен быть в цифровом формате')

        token_ya = input('Введите ваш токен сервиса Яндекс.Диск: ')

        super().__init__(token_ya)
        self.token = access_token
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def users_info(self):
        url = 'https://api.vk.com/method/users.get'
        params = {'user_ids': self.user_id}
        response = requests.get(url, params={**self.params, **params})
        return response.json()

    def vk_get_photos(self, offset=0, count=5):
        response = requests.get('https://api.vk.com/method/photos.get', params={
            'owner_id': self.user_id,
            'access_token': self.token,
            'offset': offset,
            'count': count,
            'album_id': 'profile',
            'extended': 1,
            'photo_sizes': 1,
            'v': self.version
        })
        return response.json()

    @staticmethod
    def unix_time_to_time(unix_time):
        dt = datetime.datetime.fromtimestamp(unix_time)
        return dt

    def get_files_urls(self):
        photos_data = []

        photos_response = self.vk_get_photos()
        if 'response' in photos_response and 'items' in photos_response['response']:
            for item in photos_response['response']['items']:
                human_readable_date = self.unix_time_to_time(item['date'])
                likes = item['likes']['count']
                for size in item['sizes']:
                    if size['type'] == 'z':
                        photo_url = size['url']
                        photo_info = {
                            'url': photo_url,
                            'date': human_readable_date,
                            'likes': likes
                        }
                        photos_data.append(photo_info)

        # Сортировка фотографий по количеству лайков и дате загрузки
        photos_data.sort(key=lambda x: (x['likes'], x['date']), reverse=True)

        # Создание списка имен файлов
        file_names = []
        for photo in photos_data:
            base_name = f"{photo['likes']}_likes"
            if file_names.count(base_name) > 0:
                base_name += f"_{photo['date'].strftime('%Y%m%d_%H%M%S')}"
            file_names.append(base_name)

        # Создание структуры для сохранения в JSON
        json_data = []
        for i, photo in enumerate(photos_data):
            json_data.append({
                'file_name': file_names[i],
                'url': photo['url'],
                'date': photo['date'].strftime('%Y-%m-%d %H:%M:%S'),
                'likes': photo['likes']
            })

        # Сохранение в JSON-файл
        with open('photos_data.json', 'w') as json_file:
            json.dump(json_data, json_file, indent=4)

        return json_data

    def upload_photos_to_yandex_disk(self, folder_name):
        # Создание папки на Яндекс.Диске
        self.create_folder(folder_name)

        # Получение данных о фотографиях
        photos_data = self.get_files_urls()

        # Загрузка фотографий на Яндекс.Диск
        for photo in photos_data:
            file_name = f"{photo['file_name']}.jpg"
            file_url = photo['url']
            self.put_file_to_folder(file_name, folder_name, file_url)

        print(f"Все фотографии загружены в папку {folder_name} на Яндекс.Диске.")


# Пример использования
vk_handler = VK(access_token)
vk_handler.upload_photos_to_yandex_disk("VK_Photos")
