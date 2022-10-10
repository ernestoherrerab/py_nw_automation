# Prisma SDK

The repository lives here: <https://github.com/PaloAltoNetworks/panapi>

The "Location()" class (located in panapi/config/network.py) when applied with "read()" throws an error due to the following:

~~~python
config = result['data'][0]
TypeError: list indices must be integers or slices, not str
~~~

The error is thrown due to "Location()" being forced to have a "name" attribute which does not exist in the API call and the conditional loop on line 71 of the init.py catches this and applies the following:

~~~python
config = result['data'][0]
~~~

However the result is a list of dictionaries, hence there is no key called "data" in the result causing the error.

~~~python
TypeError: list indices must be integers or slices, not str
~~~

To solve this, the following has been edited:

~~~python
    elif has_name:
        if "data" in result:
            config = result["data"][0]
            return type(self)(**config)
        else:
            return result
~~~

***
