from tns_glass.tests import TNSTestCase
from django.core.urlresolvers import reverse
from .models import *

class PhotoTest(TNSTestCase):

    def test_crudl(self):
        create_url = '%s?wetmill=%d' % (reverse('photos.photo_create'), self.nasho.id)

        # try to create photo without logging in
        response = self.client.get(create_url, follow=True)
        self.assertAtURL(response, '/users/login/')

        # ups! not possible
        self.login(self.admin)
        response = self.client.get(create_url, follow=True)

        # get main photo
        self.assertEquals(None, self.nasho.get_main_photo())

        # cause there is no main photo yet the form now includes it
        self.assertIn('is_main', response.context['form'].fields)

        # now create the first photo
        post_data = dict()
        f = open(self.build_import_path("photo_test_imagefield.png"))

        post_data['is_active']  = True
        post_data['is_main']  = True
        post_data['caption']  = "Thi is the main photo"
        post_data['image']  = f
        response = self.assertPost(create_url, post_data)

        # check if nasho wetmill has the photo now
        self.assertEquals(1, len(self.nasho.photos.all()))

        # check the form for the second wetmill photo creation
        response = self.client.get(create_url, follow=True)

        # now that the first photo is main the form won't include the field "is_main"
        self.assertNotIn('is_main', response.context['form'].fields)

        # create the second photo for this wetmill
        post_data = dict()
        f = open(self.build_import_path("photo_test_imagefield.png"))

        post_data['is_active']  = True
        post_data['caption']  = "This is second photo which is not main for now"
        post_data['image']  = f
        response = self.assertPost(create_url, post_data)

        # get the photo resolution
        photo = self.nasho.photos.all()[0]

        # now this wetmill has two photos
        self.assertEquals(2, len(self.nasho.photos.all()))
        self.assertEquals('300x199', photo.get_resolution())
        self.assertEquals(self.nasho, photo.wetmill)

        # make the image huge, test that we default to something smaller
        photo.image_width = 1000
        self.assertEquals('800x600', photo.get_resolution())

        # lets test the update
        update_url = reverse('photos.photo_update', args=[self.nasho.photos.all()[1].id])

        post_data = dict()
        f = open(self.build_import_path("photo_test_imagefield.png"))

        post_data['is_active']  = True
        post_data['caption']  = 123
        post_data['image']  = f

        # is it possible to have two main images
        post_data['is_main'] = True
        response = self.client.post(update_url, post_data, follow=True)

        # nop!
        self.assertEquals(20, response.context['messages'].level)
        self.assertIn("Currently there is an existing Photo for this wetmill which is main", response.content)

        # edit the main image
        update_url = reverse('photos.photo_update', args=[self.nasho.photos.all()[0].id])

        post_data = dict()
        f = open(self.build_import_path("photo_test_imagefield.png"))

        post_data['is_active']  = True
        post_data['is_main'] = False
        post_data['caption']  = "This is the first image which is not main anymore"
        post_data['image']  = f

        self.assertPost(update_url, post_data)

        # get photo count
        self.assertEquals(1, self.nasho.get_photo_count())

        # get non main photos
        self.assertEquals(1, len(self.nasho.get_non_main_photos()))

        # get main photo
        self.assertEquals(self.nasho.photos.all()[0], self.nasho.get_main_photo())

        # now that the first image is not main anymore
        # lets make the second image main
        update_url = reverse('photos.photo_update', args=[self.nasho.photos.all()[0].id])

        post_data = dict()
        f = open(self.build_import_path("photo_test_small.png"))

        post_data['is_active']  = True
        post_data['is_main'] = True
        post_data['caption']  = "This is second photo becoming main"
        post_data['image']  = f

        response = self.assertPost(update_url, post_data)

        # get the photo resolution
        im_res = self.nasho.photos.all()[0].get_resolution()

        # now this wetmill has two photos
        self.assertEquals(2, len(self.nasho.photos.all()))
        self.assertEquals('400x300', im_res)

        # test related methods within wetmill
        # get photo count
        self.assertEquals(1, self.nasho.get_photo_count())

        # get non main photos
        self.assertEquals(1, len(self.nasho.get_non_main_photos()))

        # get main photo
        self.assertEquals(self.nasho.photos.all()[0], self.nasho.get_main_photo())
