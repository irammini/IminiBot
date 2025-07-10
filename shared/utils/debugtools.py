# debugtools.py
import time

def timeit(label):
    def wrapper(func):
        async def inner(*args, **kwargs):
            t0 = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                dt = time.perf_counter() - t0
                print(f"⏱️ {label} took {dt:.3f} seconds")
        return inner
    return wrapper