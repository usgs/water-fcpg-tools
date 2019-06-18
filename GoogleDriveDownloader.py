import gdown
import os

urls = {1985:'1hy_EubZTXEP3MVph-Qha-BizT6Zunzq7',
1986:'1Fox2KSmkTJQtgqnAjVQ8EJKCQZp1oUaf',
1987:'1eedPZr8tV-krpYhkrtTuG09Y4Emt2chb',
1988:'1l-2kfmYZ47vnh2qOrFXHsHWKm4ZdP2Fj',
1989:'1PzHoeQCfr8koNQ02JkKckEdL2MoobSN9',
1990:'1rcmY27s1iBOj19TP7OKiIgxqpIpOZto6',
1991:'1BgFnioO94SbZAhVDQhNSz6PDAwSSVugn',
1992:'1laNOczicaTayk3KxqtTvBce0IalUmGlL',
1993:'1N5t8Xh9vWcUb15fUCfqXYaoObqFZ2uNX',
1994:'1dFKhNJhAe04XDh6nx8KEXt37YPG3_pH7',
1995:'1g5pEolGkaO5XDYIMplVZgZl7Lkc4T48e',
1996:'1Wy2R8WcULKENpTylPz0QwJDZHGPSigYR',
1997:'1VOGBxMtw0gr2WFK1mmhl7Z8kyeAv23qk',
1998:'1Z5ck1xor4DrmcAEzxRGR4pKTonkvceiC',
1999:'1uZZVsrglPl7gPcR0iZjdZjXnCwTl2KOQ',
2000:'1a39YJPM62MnJBuQNTP6TYMjDkBrfTQWp',
2001:'1g1Z12yFB93vdV1Z38p4eCNifuJJXfYdL',
2002:'1y8qo-vgrnf6BYIkXl4G08HcwbeQvn5rU',
2003:'1kFjROWBNwb9s04LLbAg9OfHkyik_k01S',
2004:'1y3OsYAvYEfWfcKCokgIcb5k58VyUBhOn',
2005:'1_fYVQ9hMGdok7XsBzlAOp2Dg25sXALHB',
2006:'1coq347H9HH6yzyF35eG9Twhw8dzMOzhN',
2007:'1AsRhb1Wyo8CgsFONvgd9geqiOYCo4pk3',
2008:'1sP7exvLFu04uM4tmfsp92jR2sks5BrFI',
2009:'1ySq1xvt1fS1NMlczw-OQZ_1T7Hs72O3I',
2010:'1a01xWSwDF6OfqNZLRXVITatxL67SUH6L',
2011:'1Bjr9ecJhvVJ-h1dvlGGKUu7oCCPwmjBw',
2012:'10bZiSFclnzO3k-4xmQq2Bjb5U9Mc4kcf',
2013:'1hrwUBHF8I6-FxLI34P3_FjlHWak7hyJx',
2014:'1Y3cT8SxaTSj4kmezq7mmz3YOA7o76Brr',
2015:'1SEiwL5YSb3GnvxmyyuQyRA13oqSXOTh9',
2016:'1d7z1Ihv5Zt96UQH66vjVwzONErxKAKKf',
2017:'15RgMUV6gSb4OA-LEVIIWgBNaNJQtLDuS',
2018:'1PJocJ1oqsnGTwsyGMWG9cO7evibdqYfW'
}

outDir = "../data/cov/NDVI"

HUC = 1003


for year, fileID in urls.items():
    outName = "LANSAT_NVDI_{0}_00_00_HUC{1}.tif".format(year, HUC)

    outpath = os.path.join(outDir, outName)
    url = "https://drive.google.com/uc?id={0}".format(fileID)
    gdown.download(url, outpath, quiet=False)
