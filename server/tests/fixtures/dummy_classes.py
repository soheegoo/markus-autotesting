class FakeQueue:

	def __init__(self, *args, **kwargs):
		args = list(args)
		self.type = args.pop(0) if args else kwargs.get('type')
		self.args = args
		self.kwargs = kwargs

	def __repr__(self):
		return f'<{self.__class__.__name__} at {id(self)} type={self.type}>'