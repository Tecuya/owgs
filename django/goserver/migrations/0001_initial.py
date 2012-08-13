# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'GameNode'
        db.create_table('goserver_gamenode', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ParentNode', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['goserver.GameNode'], null=True, blank=True)),
            ('Game', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['goserver.Game'])),
        ))
        db.send_create_signal('goserver', ['GameNode'])

        # Adding model 'GameProperty'
        db.create_table('goserver_gameproperty', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('Node', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['goserver.GameNode'])),
            ('Property', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('Value', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('goserver', ['GameProperty'])

        # Adding model 'Chat'
        db.create_table('goserver_chat', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('Name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('goserver', ['Chat'])

        # Adding model 'ChatParticipant'
        db.create_table('goserver_chatparticipant', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('Chat', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['goserver.Chat'])),
            ('Participant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('Present', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('goserver', ['ChatParticipant'])

        # Adding model 'Game'
        db.create_table('goserver_game', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('Owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('CreateDate', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('Type', self.gf('django.db.models.fields.CharField')(default='F', max_length=1)),
            ('BoardSize', self.gf('django.db.models.fields.CharField')(default='19x19', max_length=10)),
            ('Komi', self.gf('django.db.models.fields.DecimalField')(max_digits=4, decimal_places=1)),
            ('AllowUndo', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('MainTime', self.gf('django.db.models.fields.IntegerField')()),
            ('OvertimeType', self.gf('django.db.models.fields.CharField')(default='N', max_length=1)),
            ('OvertimePeriod', self.gf('django.db.models.fields.IntegerField')()),
            ('OvertimeCount', self.gf('django.db.models.fields.IntegerField')()),
            ('IsOvertimeW', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('IsOvertimeB', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('OvertimeCountW', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('OvertimeCountB', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('TimePeriodRemainW', self.gf('django.db.models.fields.DecimalField')(default='0.0', max_digits=15, decimal_places=3)),
            ('TimePeriodRemainB', self.gf('django.db.models.fields.DecimalField')(default='0.0', max_digits=15, decimal_places=3)),
            ('TurnColor', self.gf('django.db.models.fields.CharField')(default='B', max_length=1)),
            ('LastClock', self.gf('django.db.models.fields.DecimalField')(default='0.0', max_digits=15, decimal_places=3)),
            ('State', self.gf('django.db.models.fields.CharField')(default='P', max_length=1)),
            ('Winner', self.gf('django.db.models.fields.CharField')(default='U', max_length=1)),
            ('WinType', self.gf('django.db.models.fields.CharField')(default='U', max_length=1)),
            ('ScoreDelta', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=5, decimal_places=1)),
            ('FocusNode', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('PendingUndoNode', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('goserver', ['Game'])

        # Adding model 'GameParticipant'
        db.create_table('goserver_gameparticipant', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('Game', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['goserver.Game'])),
            ('Participant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('JoinDate', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('LeaveDate', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('Originator', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('Present', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('Winner', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('State', self.gf('django.db.models.fields.CharField')(default='U', max_length=1)),
            ('Editor', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('goserver', ['GameParticipant'])

        # Adding model 'UserProfile'
        db.create_table('goserver_userprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('activation_key', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('key_expires', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('DebugMode', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('EidogoPlayerMode', self.gf('django.db.models.fields.CharField')(default='S', max_length=1)),
            ('Rank', self.gf('django.db.models.fields.CharField')(default='N', max_length=3)),
        ))
        db.send_create_signal('goserver', ['UserProfile'])

    def backwards(self, orm):
        # Deleting model 'GameNode'
        db.delete_table('goserver_gamenode')

        # Deleting model 'GameProperty'
        db.delete_table('goserver_gameproperty')

        # Deleting model 'Chat'
        db.delete_table('goserver_chat')

        # Deleting model 'ChatParticipant'
        db.delete_table('goserver_chatparticipant')

        # Deleting model 'Game'
        db.delete_table('goserver_game')

        # Deleting model 'GameParticipant'
        db.delete_table('goserver_gameparticipant')

        # Deleting model 'UserProfile'
        db.delete_table('goserver_userprofile')

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
            'Komi': ('django.db.models.fields.DecimalField', [], {'max_digits': '4', 'decimal_places': '1'}),
            'LastClock': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'max_digits': '15', 'decimal_places': '3'}),
            'MainTime': ('django.db.models.fields.IntegerField', [], {}),
            'Meta': {'object_name': 'Game'},
            'OvertimeCount': ('django.db.models.fields.IntegerField', [], {}),
            'OvertimeCountB': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'OvertimeCountW': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'OvertimePeriod': ('django.db.models.fields.IntegerField', [], {}),
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