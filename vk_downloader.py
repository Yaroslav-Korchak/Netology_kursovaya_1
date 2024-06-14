import requests
import datetime
import json
from tqdm import tqdm
import logging
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
        while True:
            self.vk_id = input('Введите ваш id "Вконтакте" (только цифры): ')
            if self.vk_id.isdigit():
                break
            else:
                print('ID должен быть в цифровом формате. Пожалуйста, попробуйте снова.')

        token_ya = input('Введите ваш токен сервиса Яндекс.Диск: ')

        super().__init__(token_ya)
        self.token = access_token
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def users_info(self):
        url = 'https://api.vk.com/method/users.get'
        params = {'user_ids': self.vk_id}
        response = requests.get(url, params={**self.params, **params})
        return response.json()

    def vk_get_photos(self, offset=0, count=5):
        response = requests.get('https://api.vk.com/method/photos.get', params={
            'owner_id': self.vk_id,
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

    def get_photos_info(self):
        photos_data = []

        photos_response = self.vk_get_photos()
        if 'response' in photos_response and 'items' in photos_response['response']:
            for item in photos_response['response']['items']:
                for size in item['sizes']:
                    if size['type'] == 'z':
                        likes = item['likes']['count']
                        human_readable_date = self.unix_time_to_time(item['date']).strftime('%Y%m%d_%H%M%S')
                        file_name = f"{likes}"
                        if any(photo['file_name'] == file_name for photo in photos_data):
                            file_name += f"_{human_readable_date}"
                        photo_info = {
                            'file_name': file_name,
                            'size': size['type'],
                            'url': size['url']
                        }
                        photos_data.append(photo_info)
        filtered_photos_data = [{'file_name': photo['file_name'], 'size': photo['size']} for photo in photos_data]

        # Сохранение в JSON-файл
        with open('filtered_photos_data.json', 'w') as json_file:
            json.dump(filtered_photos_data, json_file)

        return photos_data

    def upload_photos_to_yandex_disk(self, folder_name):
        # Создание папки на Яндекс.Диске
        self.create_folder(folder_name)

        # Получение данных о фотографиях
        photos_data = self.get_photos_info()

        # Загрузка фотографий на Яндекс.Диск с прогресс-баром
        for photo in tqdm(photos_data, desc="Загрузка фотографий на Яндекс.Диск"):
            file_name = photo['file_name']
            file_url = photo['url']
            self.put_file_to_folder(file_name, folder_name, file_url)

        logging.info(f"Все фотографии загружены в папку {folder_name} на Яндекс.Диске.")


# Пример использования
vk_handler = VK(access_token)
vk_handler.upload_photos_to_yandex_disk("VK_Photos")
