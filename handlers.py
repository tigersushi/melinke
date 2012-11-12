import webapp2
import logging as log

class Handler(webapp2.RequestHandler):
	def render_mako(self,t,d):
		lookup = TemplateLookup(directories=['templates_mako'], cache_impl='memcache', cache_enabled=False)
		template = lookup.get_template(t)
		d.update({
			'logout': users.create_logout_url('/'),
			'template': t,
			# 'clients': models.getforuser(models.Client),
		})
		self.response.write(template.render(**d))

class Home(Handler):
	def get(self):
		pass
		# self.response.write(open('home.html'


app = webapp2.WSGIApplication(routes = [
	('/', Home),
], debug=True)
