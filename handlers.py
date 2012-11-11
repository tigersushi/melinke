import webapp2
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import memcache

import logging as log
import json
import ezt
import markdown
import models

from mako.lookup import TemplateLookup


class Handler(webapp2.RequestHandler):
	def changeorder(self,model,match):
	   target = db.get(self.request.get('order'))
	   mod = int(self.request.get('mod'))
	   upper = model.all().filter('%s =' % match,getattr(target,match)).filter('order =',target.order+mod).get()
	   if upper:
		   target.order = target.order+mod
		   upper.order = upper.order-mod
		   target.put()
		   upper.put()
	
	def post(self,key):
		try:
			m = db.get(self.request.get('key'))
			m.save(self.request.POST)
		except Exception as e:
			log.error('%s' % (e))

	def render(self,t,d):
		template = ezt.Template("templates/index.html")
		if 'jsfile' not in d: d['jsfile'] = ''
		d.update({'template':t})
		html = template.generate(self.response.out,d)
	
	def render_mako(self,t,d):
		lookup = TemplateLookup(directories=['templates_mako'], cache_impl='memcache', cache_enabled=False)
		template = lookup.get_template(t)
		d.update({
			'logout': users.create_logout_url('/'),
			'template': t,
			# 'clients': models.getforuser(models.Client),
		})
		self.response.write(template.render(**d))


class Organization(Handler):
	def get(self,key=""):
		trainer = models.Trainer.all().filter('user =',users.get_current_user()).get().key()
		if key:
			org = db.get(key)
		else:
			org = models.Organization(admins=[trainer],members=[trainer])
		if self.request.get('del'):
			org.delete()
			return webapp2.redirect('/trainer')
		self.render_mako('organization.html',{
			'org': org,
		})

	def post(self,key=""):
		if key:
			org = db.get(key)
		else:
			org = models.Organization()
		newkey = org.save(self.request.POST)
		return webapp2.redirect('/org/%s' % newkey)


class Trainer(Handler):
	def get(self):
		trainer = models.Trainer.all().filter('user =',users.get_current_user()).get()
		if not trainer:
			trainer = models.Trainer()
			trainer.put()
		return self.render_mako('trainer.html',{
			'trainer': trainer,
			'org': models.Organization.all().filter('members =', trainer).get(),
			'org_admin': models.Organization.all().filter('admins =', trainer).get(),
		})
	
	def post(self):
		try:
			m = models.Trainer.all().filter('user =',users.get_current_user()).get()
			m.save(self.request.POST)
		except Exception as e:
			log.error(e)
		return webapp2.redirect('/')


class Trainers(Handler):
	def get(self,key=''):
		copyfrom = None
		catlist = None
		if key:
			copyfrom = db.get(key)
			catlist = models.Category.all().filter('user =',copyfrom.user).order('name')
		trainers = models.Trainer.all().fetch(None)
		trainer = filter(lambda x: x.user == users.get_current_user(), trainers)[0]
		org = models.Organization.all().filter('members =', trainer).get()
		trainerlist = filter(lambda x: x.key() in org.members, trainers)
		self.render_mako('trainers.html', {
			'trainerlist': trainerlist,
			'org': org,
			'trainer': trainer,
			'copyfrom': copyfrom,
			'catlist': catlist,
			'catlist_user': models.getforuser(models.Category)
		})
	
	def post(self,key=''):
		source = db.get(key)
		trainer = models.Trainer.all().filter('user =',users.get_current_user()).get()
		trainer.copyfrom(source,self.request.POST.getall('ex'))
		return webapp2.redirect('/trainers/')


class Clients(Handler):
    def get(self):
		trainer = models.gettrainer()
		if not trainer:
			return webapp2.redirect('/trainer')
		if self.request.get('del'):
			# trainer.remove_from_list('client',self.request.get('del'))
			db.get(self.request.get('del')).remove()
		self.render_mako('clients.html',{
			'trainer': trainer,
		})
		models.filldefault('phasetype')
		models.filldefault('setuptype')
		models.filldefault('tempotype')
		models.filldefault('cat')


class Client(Handler):
	def get(self,key):
		if key:
			client = db.get(key)
			if self.request.get('phases'):
				self.response.write(json.dumps({
					'client': client.name,
					'phases': [p.simpleformat() for p in client.phase_set.order('order')]
				}))
				return
		else:
			client = models.Client()
		# self.render('client.html',{'client':client.format()})
		self.render_mako('client.html',{'client': client})
	
	def post(self,key):
		if key:
			client = db.get(key)
		else:
			client = models.Client()
		self.request.POST['istemplate'] = self.request.get('istemplate')
		clientkey = client.save(self.request.POST)
		# trainer = models.gettrainer()
		# trainer.add_to_list('client', clientkey)
		return webapp2.redirect('/')


class Assessment(Handler):
	def get(self,mode,key):
		client = db.get(key)
		if self.request.get('edit'):
			edit = self.request.get('edit')
			if edit == 'new':
				sheet = models.Assessment(mode=mode)
			else:
				sheet = db.get(edit)
			self.render_mako('assessment_edit.html',{
				'client': client,
				'sheet': sheet,
				'fields': sheet.fields(),
				'mode': mode,
			})
		elif self.request.get('view'):
			fields, sheets = client.get_assessments(mode)
			self.render_mako('assessment_view.html',{
				'client': client,
				'fields': fields,
				'sheets': sheets,
				'mode': mode,
			})
		elif self.request.get('del'):
			# client.remove_from_list('assessment',self.request.get('del'))
			db.get(self.request.get('del')).remove()
			return webapp2.redirect('/m/%s/%s?view=1' % (mode,key))
	
	def post(self,mode,key):
		client = db.get(key)
		try:
			sheet = db.get(self.request.POST['key'])
		except KeyError:
			sheet = models.Assessment(client=client,mode=mode)
		sheet.save(self.request.POST)
		# client.add_to_list('assessment',sheet.save(self.request.POST))
		return webapp2.redirect('/m/%s/%s?view=1' % (mode,key))



class Program(Handler):
	def get(self,key):
		client = db.get(key)
		trainer = models.gettrainer()
		# phases = client.phase_set.order('order').fetch(None)
		if self.request.get('del'):
			# client.remove_from_list('phase',self.request.get('del'))
			db.get(self.request.get('del')).remove()
			return self.redirect(key)
		elif self.request.get('order'):
			self.changeorder(models.Phase,'client')
			return self.redirect(key)
		elif self.request.get('new'):
			client.newphase()
			return self.redirect(key)
		elif self.request.get('default'):
			client.setdefaultphases()
			return self.redirect(key)
		elif self.request.get('delall'):
			client.removephases()
			return self.redirect(key)
		elif self.request.get('clone'):
			client.clonephases(self.request.get('clone'))
			return self.redirect(key)
		elif self.request.get('done'):
			db.get(self.request.get('done')).toggledone()
			return self.redirect(key)
		client.notes = markdown.markdown(client.notes)
		self.render_mako('program.html',{
			# 'clients': models.getforuser(models.Client),
			'client': client,
			'trainer': trainer,
			# 'phases': phases,
			# 'phasetypes': models.getforuser(models.PhaseType),
			# 'setuptypes': models.getforuser(models.SetupType),
			# 'tempotypes': models.getforuser(models.TempoType),
			'jsfile': 'program.js',
		})
	
	def redirect(self,key):
		return webapp2.redirect('/program/%s' % key)



class Phase(Handler):
	def get(self,key):
		phase = db.get(key)
		trainer = models.gettrainer()
		if self.request.get('newcat'):
			phase.addcat()
			return self.redirect(key)
		elif self.request.get('newex'):
			db.get(self.request.get('newex')).addex()
			return self.redirect(key)
		elif self.request.get('ordercat'):
			self.changeorder(models.PhaseCat,'phase')
			return self.redirect(key)
		elif self.request.get('orderex'):
			self.changeorder(models.PhaseEx,'phasecat')
			return self.redirect(key)
		elif self.request.get('del'):
			db.get(self.request.get('del')).remove()
			return self.redirect(key)
		elif self.request.get('clone'):
			phase.clone(self.request.get('phase'))
			return self.redirect(key)
		elif self.request.get('delall'):
			phase.removeall('phasecat')
			return self.redirect(key)
		if not phase.keyfor('homework'):
			phase.createhomework()
		phase.client.notes = markdown.markdown(phase.client.notes)
		phaseexs = phase.getexercises() 
		days = phase.getdays(phaseexs)
		self.render_mako('phase.html',{
			'phase': phase,
			'days': days,
			'client': phase.client,
			'trainer': trainer,
			'dummy': models.PhaseEx(phase=phase),
			'phaseexs': phaseexs,
			'exercises': trainer.getlist('exercise'),
			'jsfile': 'phase.js',
		})
	
	def redirect(self,key):
		return webapp2.redirect('/phase/%s' % key)
	

class Homework(Handler):
	pass


class Train(Handler):
	def get(self):
		# async
		if self.request.get('done'):
			db.get(self.request.get('done')).toggledone()
			return
		elif self.request.get('exdone'):
			db.get(self.request.get('exdone')).toggledone()
			return
		elif self.request.get('ex'):
			db.get(self.request.get('ex')).setnextweight(self.request.get('next'))
			return 
		# sync
		if self.request.get('del'):
			db.get(self.request.get('del')).remove()
			return webapp2.redirect('/')
		clients = [db.get(c).format() for c in self.request.GET.getall('allclients')]
		if self.request.get('phase'):
			phase = db.get(self.request.get('phase'))
			client = phase.client
		else:
			if self.request.get('client'):
				client = db.get(self.request.get('client'))
			else:
				client = clients[0]
			phase = client.nextphase()
		currentsession = phase.nextsession()
		if self.request.get('day'):
			currentsession.day = self.request.get('day')
			currentsession.put()
		sessions = phase.session_set.filter('order !=',currentsession.order).filter('day =',currentsession.day).order('order').fetch(None)
		sessions.append(currentsession)
		if not clients: clients = [client.format()]
		self.render('train.html',{
			'client': client.format(),
			'phase': phase.format(),
			'day': currentsession.day,
			'sessions': [s.format() for s in sessions],
			'clients': clients,
			'allclients': clients,
			'days': phase.getdays(),
			'jsfile': 'train.js',
		})


class Sessions(Handler):
	def get(self,clientkey):
		client = db.get(clientkey)
		self.render('sessions.html',{
			'client': client.format(),
			'phases': [p.format() for p in client.phase_set],
			'sessions': [s.format() for s in client.session_set]
		})


class Types(Handler):
	def post(self,action,type):
		if action == 'add':
			if type == 'phasetype':
				m = models.PhaseType()
			if type == 'setuptype':
				m = models.SetupType()
			if type == 'tempotype':
				m = models.TempoType()
			if type == 'category':
				m = models.Category()
			if type == 'exercise':
				m = models.Exercise()
				cat = db.get(self.request.get('category'))
				m.category = cat
				# key = m.save(self.request.POST)
				# cat.add_to_list('exercise',key)
				# self.response.write(key)
				# return
			if type == 'equipment':
				m = models.Equipment()
			m.trainer = models.gettrainer()
			key = m.save(self.request.POST)
			# trainer.add_to_list(type,key)
			self.response.write(key);
		else:
			try:
				db.get(self.request.POST['key']).delete()
			except Exception as e:
				log.error(e)


class Print(Handler):
	def get(self,type,key):
		if type == 'phase':
			phase = db.get(key)
			format = self.request.get('format')
			if format == 'trainer':
				days = phase.getdays()
				if len(days):
					nsess = int(phase.client.frequency/len(days))
				else:
					nsess = 1
				phase.client.notes = markdown.markdown(phase.client.notes) if phase.client.notes else ''
				stretchingstr = phase.filter_stretching()
				log.info(phase.homework)
				self.render_mako('print/trainer.html',{
					'client': phase.client,
					'phase': phase,
					# 'sessions': [s.format() for s in phase.session_set.order('order')],
					'days': days,
					'span': nsess+2,
					'hw': phase.homework,
					'sess': range(nsess),
					'stretching': stretchingstr,
				})
			if format == 'client':
				day = self.request.get('day')
				stretchingstr = phase.filter_stretching()
				phase.group()
				self.render_mako('print/client.html', {
					'client': phase.client,
					'phase': phase,
					'hw': phase.homework,
					'day': day,
					'trainer': models.gettrainer(),
					'stretching': stretchingstr,
				})
		if type == 'program':
			pass
	
	def render(self,t,d):
		template = ezt.Template("templates/print/template.html")
		d.update({'template':t})
		html = template.generate(self.response.out,d)


from mako.cache import CacheImpl, register_plugin

class MemcacheMako(CacheImpl):
	CACHE = 'makocache:%s'

	def __init__(self, cache):
		super(MemcacheMako, self).__init__(cache)
	
	def get_or_create(self, key, creation_function, **kw):
		log.info('getting cache %s' % key)
		item = memcache.get(self.CACHE % key)
		if item is None:
			item = creation_function()
			memcache.set(self.CACHE % key, item) 
		return item

	def set(self, key, value, **kwargs):
		memcache.set(self.CACHE % key, value)

	def get(self, key, **kwargs):
		return memcache.get(self.CACHE % key)

	def invalidate(self, key, **kwargs):
		memcache.delete(self.CACHE % key, None)

# optional - register the class locally
register_plugin("memcache", __name__, "MemcacheMako")


app = webapp2.WSGIApplication(routes = [
	('/', Clients),
	('/client/?(.*)/?', Client),
	('/m/(\w*)/?(.*)/?', Assessment),
	('/program/?(.*)/?', Program),
	('/phase/?(.*)/?', Phase),
	('/types/(\w*)/(.*)/?', Types),
	('/homework/(.*)/?', Homework),
	('/print/(\w*)/(.*)/?', Print),
	('/train/?', Train),
	('/sessions/?(.*)/?', Sessions),
	('/trainer/?', Trainer),
	('/trainers/?(.*)/?', Trainers),
	('/org/?(.*)/?', Organization),
], debug=True)

