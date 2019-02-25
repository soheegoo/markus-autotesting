def none(): pass

def arg(arg): pass
def args(arg1, arg2): pass
def all_args(*args): pass

def kwarg(kwarg=None): pass
def kwargs(kwarg1=None, kwarg2=None): pass
def all_kwargs(**kwargs): pass

def arg_kwarg(arg, kwarg=None): pass
def args_kwarg(arg1, arg2, kwarg=None): pass
def all_args_kwarg(*args, kwarg=None): pass

def arg_kwargs(arg, kwarg1=None, kwarg2=None): pass
def args_kwargs(arg1, arg2, kwarg1=None, kwarg2=None): pass
def all_args_kwargs(*args, kwarg1=None, kwarg2=None): pass

def arg_all_kwargs(arg, **kwargs): pass
def args_all_kwargs(arg1, arg2, **kwargs): pass
def all_args_all_kwargs(*args, **kwargs): pass

dummy_functions = {  
    none: None,
    arg: {'arg'},
    args: {'arg1', 'arg2'},
    all_args: None,
    kwarg: {'kwarg'},
    kwargs: {'kwarg1', 'kwarg2'},
    all_kwargs: None,
    arg_kwarg: {'arg', 'kwarg'},
    args_kwarg: {'arg1', 'arg2', 'kwarg'},
    all_args_kwarg: {'kwarg'},
    arg_kwargs: {'arg', 'kwarg1', 'kwarg2'},
    args_kwargs: {'arg1', 'arg2', 'kwarg1', 'kwarg2'},
    all_args_kwargs: {'kwarg1', 'kwarg2'},
    arg_all_kwargs: None,
    args_all_kwargs: None,
    all_args_all_kwargs: None
}


