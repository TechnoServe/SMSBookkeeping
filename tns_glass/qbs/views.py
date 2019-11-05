from django_quickblocks.models import *
from django_quickblocks.views import QuickBlockCRUDL
from smartmin.views import *
from django import forms

class LocalizedQuickBlockCRUDL(QuickBlockCRUDL):
    model = QuickBlock
    permissions = True
    actions = ('create', 'update', 'list')

    class Update(QuickBlockCRUDL.Update):
        fields = ('title_en_us', 'title_es', 'summary_en_us', 'summary_es', 'content_en_us', 'content_es',
                  'image', 'color', 'link', 'video_id', 'quickblock_type', 'priority', 'is_active')

        def get_success_url(self):
            return "%s?type=%d" % (reverse('qbs.quickblock_list'), self.object.quickblock_type.id)

        def derive_exclude(self):
            exclude = super(LocalizedQuickBlockCRUDL.Update, self).derive_exclude()

            block_type = self.object.quickblock_type

            if not block_type.has_summary:
                exclude.append('summary_en_us')
                exclude.append('summary_es')

            if not block_type.has_video:
                exclude.append('video_id')

            if not block_type.has_title:
                exclude.append('title_en_us')
                exclude.append('title_es')

            if not block_type.has_tags:
                exclude.append('tags')

            if not block_type.has_image:
                exclude.append('image')

            if not block_type.has_link:
                exclude.append('link')

            if not block_type.has_color:
                exclude.append('color')

            return exclude

    class Create(QuickBlockCRUDL.Create):
        grant_permissions = ('django_quickblocks.change_quickblock',)

        def get_success_url(self):
            return "%s?type=%d" % (reverse('qbs.quickblock_list'), self.object.quickblock_type.id)

        def derive_exclude(self):
            exclude = super(LocalizedQuickBlockCRUDL.Create, self).derive_exclude()

            block_type = self.get_type()
            if block_type:
                exclude.append('quickblock_type')

                if not block_type.has_summary:
                    exclude.append('summary_en_us')
                    exclude.append('summary_es')

                if not block_type.has_video:
                    exclude.append('video_id')

                if not block_type.has_title:
                    exclude.append('title_en_us')
                    exclude.append('title_es')

                if not block_type.has_tags:
                    exclude.append('tags')

                if not block_type.has_image:
                    exclude.append('image')

                if not block_type.has_link:
                    exclude.append('link')

                if not block_type.has_color:
                    exclude.append('color')

            return exclude