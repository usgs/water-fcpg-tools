import gdown
import os

urls = {11985:'1qvqrjsvn0jCYQw3ZHRB8YFuvA3mjOTMJ',
1986:'1QsmgisqdVrKtYasjXqvGGQa2y_7zcZqh',
1987:'1krqXSzHUDM7OoTPkhmTxF6QKbhRHZQoM',
1988:'12HRF-_5Tn8znt1_XdShmu2AVIm5IUNKU',
1989:'1hl8jDqVOf1u6RrItx7tLfXI_1huwKFP1',
1990:'1hOrSOtqzRcSAmaFU3Me78k41ao36oVVG',
1991:'1-wnpznyFlSZuX70EeQ4OG3Z7fbKPjHRy',
1992:'1p_vsxcgNv-Q_TYFZ31fz1KaivlIXIUuR',
1993:'1971bQcUt4RKQYDJ9w6I51XQuCMv9e9E0',
1994:'1VW2LJUkE-7mJPzvHLOs7skuOtDh0ISwx',
1995:'1ikN4pozSzk9_n8cB5soD505pcv1EY9IG',
1996:'1lWPTG2EkaltN8HDJHDHTrZkJKaIL368N',
1997:'1dsPLhVx8kZhbog88XscHhRxNloXMqx_Q',
1998:'1oLE-8BJD-bhQiafQwurFWEdvTnsZe1iU',
1999:'1FUEqaAJ-mOLQEGlY8S2d7FcbjGdUS2Li',
2000:'14K3UFMakCButQ4ypbAyKL_6lnTsJCSRi',
2001:'1Z40Fem1IHH8FvS50S3M85o2FOzj0VIu4',
2002:'1_KtmQFceePRnU52iaqexvhm8BFQSRnxO',
2003:'1_dBX7cvg_IWykvCbIPyBdnjT7cRUBKa1',
2004:'1cAVKkiIha6KGm69pZoRCcf_1Fh2GqjTS',
2005:'1yBOTzyvcPnbh0AYv-5Vh2fXJQAFru9pa',
2006:'1ivkdUJmGBhO2EahG1Bf-QAsHtaSV75m9',
2007:'1p64srTIBz09r3_aXyMBDkxVjLJUdFnCr',
2008:'1FvGnzZydKDf_jiFvutA4OwOC2mVA3D90',
2009:'1Fr8JLzsKRkTtvgCsz1SztYc01ezoAq_W',
2010:'1sJEQlFGx3Lay6S9hjIDFy_cmmvV08hG_',
2011:'1j_OPlzHu1aAWcQH4-EfDQBBU8wohD5-Q',
2012:'1StKAr2oOrFBc-OIHrn_xPV0PTBXKoz61',
2013:'18ttHsPAXEQZrsLcihfPhKAz9bt5YqNwa',
2014:'1MpgbiW2PI3HLjyx4U6CBDZMeZLY1WrIY',
2015:'1twkaoTm0QSPmDsvbU-Cgr3wrKCcBVh0E',
2016:'1sdCf1_q_bzQHVEwbF3svCDehBX9mW7Bs',
2017:'1Ko6IB_w_-W4LkfHCPTPwAJ0Y7RLsT1dl',
2018:'1dbq-3iqH8RECEifMlTNvMWqaxLnllFL-'

}

outDir = "../data/cov/NDVI"

HUC = 1002


for year, fileID in urls.items():
    outName = "LANSAT_NVDI_{0}_00_00_HUC{1}.tif".format(year, HUC)

    outpath = os.path.join(outDir, outName)
    url = "https://drive.google.com/uc?id={0}".format(fileID)
    gdown.download(url, outpath, quiet=False)
