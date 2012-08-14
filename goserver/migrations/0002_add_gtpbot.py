# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        from django.contrib.auth.models import User
        u = User(
            username='gnugo')

        # default gnugo password matches gtpbot.cfg.example
        u.set_password('insecure') 
        
        u.save()

    def backwards(self, orm):
        "Write your backwards methods here."
        from django.contrib.auth.models import User
        User.objects.get(username='gnugo').delete()

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'goserver.chat': {
            'Meta': {'object_name': 'Chat'},
            'Name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'goserver.chatparticipant': {
            'Chat': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['goserver.Chat']"}),
            'Meta': {'object_name': 'ChatParticipant'},
            'Participant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'Present': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'goserver.game': {
            'AllowUndo': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'BoardSize': ('django.db.models.fields.CharField', [], {'default': "'19x19'", 'max_length': '10'}),
            'CreateDate': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'FocusNode': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'IsOvertimeB': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'IsOvertimeW': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Komi': ('django.db.models.fields.DecimalField', [], {'default': "'5.5'", 'max_digits': '4', 'decimal_places': '1'}),
            'LastClock': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'max_digits': '15', 'decimal_places': '3'}),
            'MainTime': ('django.db.models.fields.IntegerField', [], {'default': '600'}),
            'Meta': {'object_name': 'Game'},
            'OvertimeCount': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'OvertimeCountB': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'OvertimeCountW': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'OvertimePeriod': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'OvertimeType': ('django.db.models.fields.CharField', [], {'default': "'N'", 'max_length': '1'}),
            'Owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'PendingUndoNode': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ScoreDelta': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '5', 'decimal_places': '1'}),
            'State': ('django.db.models.fields.CharField', [], {'default': "'P'", 'max_length': '1'}),
            'TimePeriodRemainB': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'max_digits': '15', 'decimal_places': '3'}),
            'TimePeriodRemainW': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'max_digits': '15', 'decimal_places': '3'}),
            'TurnColor': ('django.db.models.fields.CharField', [], {'default': "'B'", 'max_length': '1'}),
            'Type': ('django.db.models.fields.CharField', [], {'default': "'F'", 'max_length': '1'}),
            'WinType': ('django.db.models.fields.CharField', [], {'default': "'U'", 'max_length': '1'}),
            'Winner': ('django.db.models.fields.CharField', [], {'default': "'U'", 'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'goserver.gamenode': {
            'Game': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['goserver.Game']"}),
            'Meta': {'object_name': 'GameNode'},
            'ParentNode': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['goserver.GameNode']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'goserver.gameparticipant': {
            'Editor': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Game': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['goserver.Game']"}),
            'JoinDate': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'LeaveDate': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'Meta': {'object_name': 'GameParticipant'},
            'Originator': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Participant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'Present': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'State': ('django.db.models.fields.CharField', [], {'default': "'U'", 'max_length': '1'}),
            'Winner': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'goserver.gameproperty': {
            'Meta': {'object_name': 'GameProperty'},
            'Node': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['goserver.GameNode']"}),
            'Property': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'Value': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'goserver.userprofile': {
            'DebugMode': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'EidogoPlayerMode': ('django.db.models.fields.CharField', [], {'default': "'S'", 'max_length': '1'}),
            'Meta': {'object_name': 'UserProfile'},
            'Rank': ('django.db.models.fields.CharField', [], {'default': "'N'", 'max_length': '3'}),
            'activation_key': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key_expires': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['goserver']
    symmetrical = True
