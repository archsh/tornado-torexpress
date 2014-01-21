import tornado.web


class Route(object):
    """
    decorates RequestHandlers and builds up a list of routables handlers

    Tech Notes (or "What the *@# is really happening here?")
    --------------------------------------------------------

    Everytime @route('...') is called, we instantiate a new route object which
    saves off the passed in URI.  Then, since it's a decorator, the function is
    passed to the route.__call__ method as an argument.  We save a reference to
    that handler with our uri in our class level routes list then return that
    class to be instantiated as normal.

    Later, we can call the classmethod route.get_routes to return that list of
    tuples which can be handed directly to the tornado.web.Application
    instantiation.

    Example
    -------

    @route('/some/path')
    class SomeRequestHandler(RequestHandler):
        def get(self):
            goto = self.reverse_url('other')
            self.redirect(goto)

    # so you can do myapp.reverse_url('other')
    @route('/some/other/path', name='other')
    class SomeOtherRequestHandler(RequestHandler):
        def get(self):
            goto = self.reverse_url('SomeRequestHandler')
            self.redirect(goto)

    my_routes = route.get_routes()

    Credit
    -------
    Jeremy Kelley - initial work
    Peter Bengtsson - redirects, named routes and improved comments
    Ben Darnell - general awesomeness
    """

    _routes = []

    def __init__(self, uri, name=None):
        self._uri = uri
        self.name = name

    def __call__(self, _handler):
        """gets called when we class decorate"""
        name = self.name or _handler.__name__
        if not self._uri:
            pattern = r'/(?P<relpath>.*)'
        else:
            pattern = self._uri + r'(?P<relpath>.*)'
        self._routes.append(tornado.web.url(pattern, _handler, name=name))
        return _handler

    @classmethod
    def get_routes(klass):
        return klass._routes

# route_redirect provided by Peter Bengtsson via the Tornado mailing list
# and then improved by Ben Darnell.
# Use it as follows to redirect other paths into your decorated handler.
#
#   from routes import route, route_redirect
#   route_redirect('/smartphone$', '/smartphone/')
#   route_redirect('/iphone/$', '/smartphone/iphone/', name='iphone_shortcut')
#   @route('/smartphone/$')
#   class SmartphoneHandler(RequestHandler):
#        def get(self):
#            ...


def route_redirect(from_, to, name=None):
    Route._routes.append(tornado.web.url(
        from_,
        tornado.web.RedirectHandler,
        dict(url=to),
        name=name ))