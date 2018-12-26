from __future__ import unicode_literals

from django.core.files.storage import default_storage
from django.db import models
from django.db.models import signals

import subprocess

from videokit.apps import VideokitConfig

from videokit.cache import get_videokit_cache_backend

from videokit.fields import VideoFieldFile
from videokit.fields import VideoFileDescriptor
from videokit.fields import VideoSpecFieldFile
from videokit.fields import VideoSpecFileDescriptor

from videokit.forms import VideoField as VideoFormField

from django.core.checks import Error


class VideoField(models.FileField):
    attr_class = VideoFieldFile
    descriptor_class = VideoFileDescriptor
    description = 'Video'
    
    def __init__(   self, verbose_name = None, name = None, 
                    width_field = None, height_field = None, 
                    rotation_field = None,
                    mimetype_field = None,
                    duration_field = None,
                    thumbnail_field = None,
                    **kwargs):
        self.width_field = width_field
        self.height_field = height_field
        self.rotation_field = rotation_field
        self.mimetype_field = mimetype_field
        self.duration_field = duration_field
        self.thumbnail_field = thumbnail_field

        super(VideoField, self).__init__(verbose_name, name, **kwargs)

    def check(self, **kwargs):
        errors = super(VideoField, self).check(**kwargs)
        errors.extend(self._check_video_utils_installed())
        return errors

    def _check_video_utils_installed(self):
        command = 'which ffmpeg'
        response = subprocess.call(command, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        if response != 0:
            return [        
                Error(
                    'ffmpeg is not installed',
                    hint = ('Install FFMPEG from https://www.ffmpeg.org'),
                    obj = self,
                )
            ]

        command = 'which mediainfo'
        response = subprocess.call(command, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        if response != 0:
            return [        
                Error(
                    'mediainfo is not installed',
                    hint = ('Install Mediainfo from https://mediaarea.net'),
                    obj = self,
                )
            ]

        return []
        
    def deconstruct(self):
        name, path, args, kwargs = super(VideoField, self).deconstruct()
        if self.width_field:
            kwargs['width_field'] = self.width_field

        if self.height_field:
            kwargs['height_field'] = self.height_field

        if self.rotation_field:
            kwargs['rotation_field'] = self.rotation_field

        if self.mimetype_field:
            kwargs['mimetype_field'] = self.mimetype_field

        if self.duration_field:
            kwargs['duration_field'] = self.duration_field

        if self.thumbnail_field:
            kwargs['thumbnail_field'] = self.thumbnail_field

        return name, path, args, kwargs

    def contribute_to_class(self, cls, name, **kwargs):
        super(VideoField, self).contribute_to_class(cls, name, **kwargs)

        if not cls._meta.abstract:
            signals.post_init.connect(self.update_dimension_fields, sender = cls)
            signals.post_init.connect(self.update_rotation_field, sender = cls)
            signals.post_init.connect(self.update_mimetype_field, sender = cls)
            signals.post_init.connect(self.update_duration_field, sender = cls)
            signals.post_init.connect(self.update_thumbnail_field, sender = cls)

    def update_dimension_fields(self, instance, force = False, *args, **kwargs):
        has_dimension_fields = self.width_field or self.height_field
        if not has_dimension_fields:
            return

        file = getattr(instance, self.attname)

        if not file and not force:
            return

        dimension_fields_filled = not(
            (self.width_field and not getattr(instance, self.width_field))
            or (self.height_field and not getattr(instance, self.height_field)))

        if dimension_fields_filled and not force:
            return

        if file:
            width = file.width
            height = file.height
        else:
            width = None
            height = None

        if self.width_field:
            setattr(instance, self.width_field, width)
        if self.height_field:
            setattr(instance, self.height_field, height)

    def update_rotation_field(self, instance, force = False, *args, **kwargs):
        has_rotation_field = self.rotation_field
        if not has_rotation_field:
            return

        file = getattr(instance, self.attname)

        if not file and not force:
            return

        rotation_field_filled = not(self.rotation_field and not getattr(instance, self.rotation_field))

        if rotation_field_filled and not force:
            return

        if file:
            rotation = file.rotation
        else:
            rotation = None

        if self.rotation_field:
            setattr(instance, self.rotation_field, rotation)

    def update_mimetype_field(self, instance, force = False, *args, **kwargs):
        has_mimetype_field = self.mimetype_field
        if not has_mimetype_field:
            return

        file = getattr(instance, self.attname)
    
        if not file and not force:
            return

        mimetype_field_filled = not(self.mimetype_field and not getattr(instance, self.mimetype_field))
        
        if mimetype_field_filled and not force:
            return

        if file:
            mimetype = file.mimetype
        else:
            mimetype = None

        if self.mimetype_field:
            setattr(instance, self.mimetype_field, mimetype)
        
    def update_duration_field(self, instance, force = False, *args, **kwargs):
        has_duration_field = self.duration_field
        if not has_duration_field:
            return

        file = getattr(instance, self.attname)
        
        if not file and not force:
            return

        duration_field_filled = not(self.duration_field and not getattr(instance, self.duration_field))

        if duration_field_filled and not force:
            return

        if file:
            duration = file.duration
        else:
            duration = None

        if self.duration_field:
            setattr(instance, self.duration_field, duration)
    
    def update_thumbnail_field(self, instance, force = False, *args, **kwargs):
        has_thumbnail_field = self.thumbnail_field
        if not has_thumbnail_field:
            return

        file = getattr(instance, self.attname)

        if not file and not force:
            return

        thumbnail_field_filled = not(self.thumbnail_field and not getattr(instance, self.thumbnail_field))

        if thumbnail_field_filled and not force:
            return

        if file:
            thumbnail = file.thumbnail
        else:
            thumbnail = None

        if self.thumbnail_field:
            setattr(instance, self.thumbnail_field, thumbnail)

    def formfield(self, **kwargs):
        defaults = { 'form_class' : VideoFormField }
        defaults.update(kwargs)
        return super(VideoField, self).formfield(**defaults)

class VideoSpecField(VideoField):
    attr_class = VideoSpecFieldFile
    descriptor_class = VideoSpecFileDescriptor

    def __init__(   self, verbose_name = None, name = None,
                    source = None,
                    format = VideokitConfig.VIDEOKIT_DEFAULT_FORMAT,
                    storage = None,
                    video_cache_backend = None,
                    **kwargs):
        self.source = source
        self.format = format
        self.storage = storage or default_storage
        self.video_cache_backend = video_cache_backend or get_videokit_cache_backend()

        kwargs.pop('blank', None)
        kwargs.pop('null', None)

        if not format in VideokitConfig.VIDEOKIT_SUPPORTED_FORMATS:
            raise ValueError('Video format \'%s\' is not supported at this time by videokit.' % format)

        super(VideoSpecField, self).__init__(verbose_name, name, blank = True, null = True, **kwargs)

    def form_field(self, **kwargs):
        return None
