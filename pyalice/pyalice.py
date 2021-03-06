import json
import requests
from datetime import datetime, timedelta
from datedelta import datedelta
import pytz

_DEFAULT_STRING = None
_DEFAULT_NUMBER = 0
IMAGE_CARD = 'BigImage'
ITEMSLIST_CARD = 'ItemsList'
_STATUS_URL = 'https://dialogs.yandex.net/api/v1/status'
_IMAGES_URL = 'https://dialogs.yandex.net/api/v1/skills/%s/images'
_DELETE_IMAGES = 'https://dialogs.yandex.net/api/v1/skills/%s/images/%s'

YA_FIO = 'YANDEX.FIO'
YA_GEO = 'YANDEX.GEO'
YA_DT = 'YANDEX.DATETIME'
YA_NUMBER = 'YANDEX.NUMBER'

class ImageManager(object):

    def __init__(self, oAuth, skill_id):
        self.oAuth = oAuth
        self.skill_id = skill_id
        self.quota = None
        self.images = []

    def check_space(self):
        header = {'Authorization': f'OAuth {self.oAuth}'}
        r = requests.get(_STATUS_URL, headers=header)
        if r.status_code != 200:
            raise Exception('Failed to get quota information.')
        quota = json.loads(r.text)['images']['quota']
        self.quota = Quota(quota['total'], quota['used'])
        return self.quota

    def get_images(self):
        header = {'Authorization': f'OAuth {self.oAuth}'}
        r = requests.get(_IMAGES_URL % self.skill_id, headers=header)
        if r.status_code != 200:
            raise Exception('Failed to get images.')
        self.images = []
        images = json.loads(r.text)['images']
        for image in images:
            self._get_parsed_img(image)
        return self.images

    def image_from_web(self, url):
        data = json.dumps({'url': url})
        headers = {'Authorization': f'OAuth {self.oAuth}', 'Content-Type': 'application/json'}
        r = requests.post(_IMAGES_URL % self.skill_id, data=data, headers = headers)
        if r.status_code != 201:
            raise Exception(f'Failed to upload the image {url}')
        image = json.loads(r.text)['image']        
        image_parsed = self._get_parsed_img(image)
        return image_parsed

    def image_from_file(self, img_file):
        try:
            files = {'file': open(img_file, 'rb')}
        except:
            raise Exception(f'Failed to read the file {img_file}.')
        headers = {'Authorization': f'OAuth {self.oAuth}'}
        r = requests.post(_IMAGES_URL % self.skill_id, files=files, headers = headers)
        if r.status_code != 201:
            raise Exception(f'Failed to upload the image.')
        image = json.loads(r.text)['image']
        image_parsed = self._get_parsed_img(image)
        return image_parsed

    def delete_image(self, id):
        headers = {'Authorization': f'OAuth {self.oAuth}'}
        r = requests.delete(_DELETE_IMAGES % (self.skill_id, id), headers = headers)
        if r.status_code == 404:
            raise Exception(f'The image with id {id} was not found.')
        if r.status_code != 200:
            raise Exception(f'Failed to delete the image with id {id}.')
        result = json.loads(r.text)['result']
        if result == 'ok':
            self.images = [x for x in self.images if x.id != id]
        return result

    def fetch(self):
        self.check_space()
        self.get_images()

    def _get_parsed_img(self, d):
        img = ImageIM(d['id'], d.get('origUrl', None))
        self.images.append(img)
        return img

    def delete_all_image(self):
        for image in self.images:
            self.delete_image(image.id)

class ImageIM(object):

    def __init__(self, id, origUrl):
        self.id = id
        self.orig_url = origUrl

class Quota(object):

    def __init__(self, total, used):
        self.total = total
        self.used = used

class Out(object):

    def __init__(self, incoming, text = None, tts = None, card = None, end = False, buttons = None):
        self.response = Response(text, tts, card, buttons, end)
        self.session = _SessionR(incoming.session)
        self.version = incoming.version

    def add_button(self, text = None, url = None, payload = {}, hide=False):
        if (self.response.buttons == None):
            self.response.buttons = []
        self.response.buttons.append(TipButton(text, url, payload, hide))
        return self

    def add_image_card(self, image_id = None, title = None, description = None, Button = None):
            self.response.card = BigImage(image_id, title, description, Button)
            return self

    def add_items_card(self, images = [], header = None, footer = None):
            self.response.card = ItemsList(images, header, footer)
            return self
    
    def add_header(self, text):
        self.response.card.header = Header(text)
        return self

    def add_image(self, image_id = None, title = None, description = None, button = None):
        image = ImageItem(image_id, title, description, button)
        self.response.card.items.append(image)
        return self

    def add_footer(self, text, button = None):
        self.response.card.footer = Footer(text, button)
        return self

    def add_footer_button(self, text, url = None, payload = {}, hide=False):
        self.response.card.footer.button = FooterButton(text, url, payload)
        return self

    def add_image_button(self, text = None, url = None, payload = {}):
        img = self.response.card.items[-1] if self.response.card.type == ITEMSLIST_CARD else self.response.card
        img.add_button(text, url, payload)
        return self

    def build_json(self):
        return json.dumps(self, cls=RequestEncoder, ensure_ascii=False)

class Response(object):

    def __init__(self, text = None, tts = None, card = None, buttons = None, end = False):
        self.text = text
        self.tts = tts
        self.card = card
        self.buttons = buttons
        self.end_session = end

    def add_tip_button(self, text = None, url = None, payload = {}, hide=False):
        if (self.buttons == None):
            self.buttons = []
        self.buttons.append(TipButton(text, url, payload, hide))
        return self

    def add_image_card(self, image_id = None, title = None, description = None, Button = None):
            self.card = BigImage(image_id, title, description, Button)
            return self

    def add_items_card(self, images = [], header = None, footer = None):
            self.card = ItemsList(images, header, footer)
            return self
    
    def add_header(self, text):
        self.card.header = Header(text)
        return self

    def add_image(self, image_id = None, title = None, description = None, button = None):
        image = ImageItem(image_id, title, description, button)
        self.card.items.append(image)
        return self

    def add_footer(self, text, button = None):
        self.card.footer = Footer(text, button)
        return self

    def add_footer_button(self, text, url = None, payload = {}, hide=False):
        self.card.footer.button = FooterButton(text, url, payload)
        return self

    def add_image_button(self, text = None, url = None, payload = {}):
        img = self.card.items[-1] if self.card.type == ITEMSLIST_CARD else self.card
        img.add_button(text, url, payload)
        return self

class _SessionR(object):

    def __init__(self, session):
        self.session_id = session.session_id
        self.message_id = session.message_id
        self.user_id = session.user_id

class _ButtonBase(object):

    def __init__(self, url = None, payload = {}):
        self.url = url
        self.payload = payload

class ImageButton(_ButtonBase):

    def __init__(self, text = None, url = None, payload = {}):
        self.text = text
        super().__init__(url, payload)

class FooterButton(_ButtonBase):

    def __init__(self, text, url = None, payload = {}):
        self.text = text
        super().__init__(url, payload)

class TipButton(_ButtonBase):

    def __init__(self, title, url = None, payload = {}, hide = True):
        self.title = title
        super().__init__(url, payload)
        self.hide = hide

class Header(object):

    def __init__(self, text):
        self.text = text

class Footer(object):

    def __init__(self, text, button = None):
        self.text = text
        self.button = button

class ImageItem(object):

    def __init__(self, image_id = None, title = None, description = None, button = None):
        self.image_id = image_id
        self.title = title
        self.description = description
        self.button = button

    def add_button(self, text = None, url = None, payload = {}):
        self.button = ImageButton(text, url, payload)

class BigImage(ImageItem):

    def __init__(self, image_id, title = None, description = None, button = None):
        self.type = IMAGE_CARD
        super().__init__(image_id, title, description, button)

class ItemsList(object):

    def __init__(self, items = [], header = None, footer = None):
        self.type = ITEMSLIST_CARD
        self.header = header
        self.items = items
        self.footer = footer

class RequestEncoder(json.JSONEncoder):
    def default(self, obj): # pylint: disable=E0202
        if (isinstance(obj, Out)):
            result = {}
            response = {}
            result['response'] = response
            response['text'] = obj.response.text
            if (obj.response.tts is not None):
                response['tts'] = obj.response.tts
            if (obj.response.card is not None):
                card = {}
                response['card'] = card
                card['type'] = obj.response.card.type
                if isinstance(obj.response.card, BigImage):
                    self.build_card(obj.response.card, card)
                elif isinstance(obj.response.card, ItemsList):
                    if (obj.response.card.header is not None):
                        card['header'] = self.to_dict(obj.response.card.header)
                    items = []
                    card['items'] = items
                    for item in obj.response.card.items:
                        items.append(self.build_card(item))
                    if (obj.response.card.footer is not None):
                        if (obj.response.card.footer.button):
                            obj.response.card.footer.button = self.to_dict(obj.response.card.footer.button)
                        card['footer'] = self.to_dict(obj.response.card.footer)
               
            if (obj.response.buttons is not None):
                buttons = []
                for but in obj.response.buttons:
                    buttons.append(self.to_dict(but))
                response['buttons'] = buttons
            
            response['end_session'] = obj.response.end_session 
            result['session'] = self.to_dict(obj.session)
            result['version'] = obj.version
            return result
        return json.JSONEncoder.default(self, obj)
    
    def build_card(self, card_obj, card = None):
        if card is None:
            card = {}
        if (card_obj.image_id is not None):
            card['image_id'] = card_obj.image_id
        if (card_obj.title is not None):
            card['title'] = card_obj.title
        if (card_obj.description is not None):
            card['description'] = card_obj.description
        if (card_obj.button is not None):
            card['button'] = self.to_dict(card_obj.button)
        return card

    def to_dict(self, obj):
        result = {}
        for k, v in obj.__dict__.items():
            if (v is not None):
                result[k] = v
        return result     

class In(object):

    def __init__(self, j):
        self.meta = _Meta(j['meta'])
        self.request = _Request(j['request'])
        self.session = _Session(j['session'])
        self.version = j['version']

    def get_entities(self, ya_type):
        return [x for x in self.request.nlu.entities if x.type == ya_type]

class _Request(object):

    def __init__(self, j):
        self.command = j.get('command', _DEFAULT_STRING)
        self.original_utterance = j['original_utterance']
        self.type = j['type']
        if 'markup' in j:
            self.markup = list(j['markup'].keys())
        self.payload = j.get('payload', None)
        self.nlu = _nlu(j['nlu'])

class _Meta(object):

    def __init__(self, j):
        self.locale = j['locale']
        self.timezone = j['timezone']
        self.client_id = j['client_id']
        if 'interfaces' in j:
            self.interfaces = list(j['interfaces'].keys())

class _nlu(object):

    def __init__(self, j):
        self.tokens = j['tokens']
        self.entities = _Entities(j['entities']).entites

class _Entities(object):

    def __init__(self, j):
        self.entites = []
        for ent in j:
            if ent['type'] == YA_FIO:
                self.entites.append(_Fio(ent))
            if ent['type'] == YA_GEO:
                self.entites.append(_Geo(ent))
            if ent['type'] == YA_DT:
                self.entites.append(_DateTime(ent))
            if ent['type'] == YA_NUMBER:
                self.entites.append(_Number(ent))                

class _Session(object):

    def __init__(self, j):
        self.new = j['new']
        self.message_id = j['message_id']
        self.session_id = j['session_id']
        self.skill_id = j['skill_id']
        self.user_id = j['user_id']

class _Entity(object):

    def __init__(self, j):
        self.type = j['type']
        self.tokens = _EntityTokens(j['tokens'])

class _EntityTokens(object):
    def __init__(self, j):
        self.start = j['start']
        self.end = j['end']

class _Fio(_Entity):

    def __init__(self, j):
        super().__init__(j)
        self.value = _FioFields(j['value'])

class _Geo(_Entity):

    def __init__(self, j):
        super().__init__(j)
        self.value = _GeoFields(j['value'])

class _DateTime(_Entity):

    def __init__(self, j):
        super().__init__(j)
        self.value = _DateTimeFields(j['value'])

    def get_datetime(self, tz):
        tzone = pytz.timezone(tz)
        dt_loc = datetime.now(tzone)
        offset_delta = dt_loc.utcoffset()
        offset = int(offset_delta.total_seconds() / 3600)
        timeset = True
        if self.value.year_is_relative == True:
            dt_loc = dt_loc + datedelta(years=self.value.year)
        elif self.value.year_is_relative == False:
            dt_loc = dt_loc.replace(year=self.value.year)

        if self.value.month_is_relative == True:
            dt_loc = dt_loc + datedelta(months=self.value.month)
        elif self.value.month_is_relative == False:
            dt_loc = dt_loc.replace(month=self.value.month)

        if self.value.day_is_relative == True:
            dt_loc = dt_loc + timedelta(days=self.value.day)
        elif self.value.day_is_relative == False:
            dt_loc = dt_loc.replace(day=self.value.day)

        if self.value.hour_is_relative == True:
            dt_loc = dt_loc + timedelta(hours=self.value.hour)
        elif self.value.hour_is_relative == False:
            dt_loc = dt_loc.replace(hour=self.value.hour)
        else:
            timeset = False

        if self.value.minute_is_relative == True:
            dt_loc = dt_loc + timedelta(minutes=self.value.minute)
            timeset = True
        elif self.value.minute_is_relative == False:
            dt_loc = dt_loc.replace(minute=self.value.minute)
            timeset = True
        else:
            dt_loc = dt_loc.replace(minute=0)

        if timeset == False:
            dt_loc = dt_loc.replace(hour=23, minute=0)

        return dt_loc, offset

class _Number(_Entity):

    def __init__(self, j):
        super().__init__(j)
        self.value = j['value']

class _FioFields(object):
    def __init__(self, j):
        self.first_name = j.get('first_name', _DEFAULT_STRING)
        self.patronymic_name = j.get('patronymic_name', _DEFAULT_STRING)
        self.last_name = j.get('last_name', _DEFAULT_STRING)

class _GeoFields(object):
    def __init__(self, j):
        self.country = j.get('country', _DEFAULT_STRING)
        self.city = j.get('city', _DEFAULT_STRING)
        self.street = j.get('street', _DEFAULT_STRING)
        self.house_number = j.get('house_number', _DEFAULT_STRING)
        self.airport = j.get('airport', _DEFAULT_STRING)

class _DateTimeFields(object):
    
    def __init__(self, j):
        self.year = j.get('year', _DEFAULT_NUMBER)
        self.year_is_relative = j.get('year_is_relative', None)
        self.month = j.get('month', _DEFAULT_NUMBER)
        self.month_is_relative = j.get('month_is_relative', None)
        self.day = j.get('day', _DEFAULT_NUMBER)
        self.day_is_relative = j.get('day_is_relative', None)
        self.hour = j.get('hour', _DEFAULT_NUMBER)
        self.hour_is_relative = j.get('hour_is_relative', None)
        self.minute = j.get('minute', _DEFAULT_NUMBER)
        self.minute_is_relative = j.get('minute_is_relative', None)
