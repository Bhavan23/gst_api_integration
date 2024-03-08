# Copyright (c) 2023, aerele and contributors
# For license information, please see license.txt

import frappe
from erpnext.regional.report.gstr_2.gstr_2 import Gstr2Report

from gst_api_integration.gst_api_integration.doctype.gstr_1_report.gstr_1_report import get_access_token
from gst_api_integration.gst_api_integration.doctype.api_log.api_log import create_api_log
from random import randint
from frappe.utils import getdate, random_string, cstr, flt

import json
import requests

ACTIONS = {
    "B2B": "B2B",
     "CDNR": "CDN"
     }

def execute(filters=None):
    global datas
    columns, datas = Gstr2Report(filters).run()
    
    # print(columns, datas, "columns, datas" )

    action = ACTIONS.get(filters.get('type_of_business'))

    #map data with purchase invoice no
    mapped_data = {row:
                [data[0],
                frappe.get_value("Purchase Invoice", data[1], "bill_no") or "",
                str(frappe.utils.getdate(data[2])), data[3]
                ] for row, data in enumerate(datas)}
    
    # print(mapped_data, "mapped_data")

    if filters.get('filed') or filters.get('not_filed'):

        gst_data =  get_gstr2_data(filters, action) or []
        
        # print(gst_data, "gst_data" )

        map_gst_data = []
  
        for data in gst_data:
            gstin = [data.get('ctin'),]
            for inv in data.get('inv'):
                idt = str(frappe.utils.getdate(inv.get('idt')))
                
                main_value = [
                    inv.get('inum'), idt, flt(inv.get('val'))
                ]
                map_gst_data.append(gstin + main_value)
                
        # print(map_gst_data, 'map_gst_data')

        filed = 1 if filters.get('filed') else 0
        # print(map_gst_data)

        datas = filter_data(mapped_data, map_gst_data, filed)
  
        # print(mapped_data)

    return columns, datas

def filter_data(mapped_data, gst_data, filed):
    
    # print(gst_data, mapped_data, filed, sep= "\n\n" )
    
    row_map = {row: data for row, data in enumerate(datas)}
 
    def get_value(data):
        data[1:2] = [None]
        return data

    with_out_invoice = [get_value(list(data)) for data in gst_data]
    
    print(with_out_invoice, "with_out_invoice")
 
    for key in mapped_data:
        print(key , "key")
        # print(mapped_data[key] , gst_data)
        
        if filed:
            print(mapped_data[key] ,  gst_data)
            if mapped_data[key] not in gst_data:
                print(mapped_data[key],"\n",)
                # print("gets", gst_data, "end")
                # print("if")
                if mapped_data[key] not in with_out_invoice:
                    # print("yes")
                    row_map.pop(key)
                    # print("yes")
            # else:
            #     print("else")
            #     print(mapped_data[key])
        else:
            if mapped_data[key] in gst_data:
                if mapped_data[key] in with_out_invoice:
                    row_map.pop(key)
                    # print("no")
    # print(row_map)
    return list(row_map.values())


def get_gstr2_data(filters, action):
    gst_data =  [{"inv": [{"val": 766, "itms": [{"num": 1, "itm_det": {"csamt": 0, "samt": 0, "rt": 12, "txval": 683.94, "camt": 0, "iamt": 82.07}}], "inv_typ": "R", "pos": "33", "idt": "03-01-2024", "rchrg": "N", "inum": "IN-708", "chksum":
"9ae5d72eecdf8fcd8ade261e72c530a9e0754d7b81ee6e6a2127c0b47453969b"}], "cfs": "Y", "ctin": "23AJEPM9346G1Z5", "fldtr1": "10-Feb-24", "cfs3b": "N", "flprdr1": "Jan-24"}, {"inv": [{"val": 41.3, "itms": [{"num": 1, "itm_det": {"rt": 18,
"txval": 35, "iamt": 6.3}}], "inv_typ": "R", "pos": "33", "idt": "31-01-2024", "rchrg": "N", "inum": "151241", "chksum": "b5c3d84f30e5c634b79f6526223818f3029e1a059714022edf5b1b1e4e8f60a0"}], "cfs": "Y", "ctin": "29AAKCR4702K1Z1", "fldtr1":
"11-Feb-24", "cfs3b": "N", "flprdr1": "Jan-24"}, {"inv": [{"val": 864154, "itms": [{"num": 1, "itm_det": {"csamt": 0, "samt": 0, "rt": 28, "txval": 675120, "camt": 0, "iamt": 189033.59}}], "inv_typ": "R", "irn":
"5fa5fd634a6e623abe6f7b80e7e610578c86ad4bc722d2f12dd3a7aba0dccdb6", "srctyp": "E-Invoice", "pos": "33", "idt": "04-01-2024", "rchrg": "N", "irngendate": "05-01-2024", "inum": "25/TYRE/2023-24", "chksum":
"171b3e0f9f24a1705081335a8349e727e606108dc3af68a45aef999df7b7cc7f"}], "cfs": "Y", "ctin": "34AAFFU7373M1ZL", "fldtr1": "10-Feb-24", "cfs3b": "N", "flprdr1": "Jan-24"}, {"inv": [{"val": 20.69, "itms": [{"num": 1, "itm_det": {"csamt": 0,
"samt": 0, "rt": 18, "txval": 17.53, "camt": 0, "iamt": 3.16}}], "inv_typ": "R", "irn": "73f9d6d520fd1bbc2858eb97b8b30a4b49257fcacf6b3f19bd8927d785cef74e", "srctyp": "E-Invoice", "pos": "33", "idt": "31-01-2024", "rchrg": "N", "irngendate":
"02-02-2024", "inum": "4910584154", "chksum": "abbd262aa1fdc078ea705dd15ec4a164d999c07f0c068101252fbb9414b463a5"}], "cfs": "Y", "ctin": "27AAGCG4576J1Z6", "fldtr1": "11-Feb-24", "cfs3b": "N", "flprdr1": "Jan-24"}, {"inv": [{"val": 15264,
"itms": [{"num": 1800, "itm_det": {"rt": 18, "txval": 12936, "iamt": 2328.48}}], "inv_typ": "R", "pos": "33", "idt": "31-01-2024", "rchrg": "N", "inum": "CSLLP392324", "chksum":
"7b633f8c66cb992549d88bc11d84b27435dd2943ff88466094cdcebf00683cc7"}], "cfs": "Y", "ctin": "29AAOFC8017H1Z5", "fldtr1": "10-Feb-24", "cfs3b": "N", "flprdr1": "Jan-24"}, {"inv": [{"val": 14000, "itms": [{"num": 1, "itm_det": {"csamt": 0,
"samt": 1067.76, "rt": 18, "txval": 11864, "camt": 1067.76, "iamt": 0}}], "inv_typ": "R", "irn": "5ea8ec668f06870cbf84f1fa34b5f1f6a1bf8b396873527028d331f6699458e3", "srctyp": "E-Invoice", "pos": "33", "idt": "01-01-2024", "rchrg": "N",
"irngendate": "01-01-2024", "inum": "CWPSI2324-08902", "chksum": "73cd9c19f931dd54ff5b2813e48d4083e461094168f864a1dc48b870b4d7e8fa"}, {"val": 14000, "itms": [{"num": 1, "itm_det": {"csamt": 0, "samt": 1067.76, "rt": 18, "txval": 11864,
"camt": 1067.76, "iamt": 0}}], "inv_typ": "R", "irn": "1feccded61cc0b5cfbe7a9bc91775661eaaf7e115c2363856e67a581a74a04f8", "srctyp": "E-Invoice", "pos": "33", "idt": "04-01-2024", "rchrg": "N", "irngendate": "04-01-2024", "inum":
"CWPSI2324-08997", "chksum": "d8d939b2aab07a5c3d053079f944d54fbdfc1a1a014b8b8db5741032f0f3d1a4"}, {"val": 14000, "itms": [{"num": 1, "itm_det": {"csamt": 0, "samt": 1067.76, "rt": 18, "txval": 11864, "camt": 1067.76, "iamt": 0}}],
"inv_typ": "R", "irn": "15b4112a15a6e7aee7ff44307f088154d746310c6b3cd7006caea8470032974c", "srctyp": "E-Invoice", "pos": "33", "idt": "09-01-2024", "rchrg": "N", "irngendate": "09-01-2024", "inum": "CWPSI2324-09101", "chksum":
"cc356a753ad9e36d2675e49018120c0706413cbee0b1fe02fb508017825318f9"}, {"val": 14000, "itms": [{"num": 1, "itm_det": {"csamt": 0, "samt": 1067.76, "rt": 18, "txval": 11864, "camt": 1067.76, "iamt": 0}}], "inv_typ": "R", "irn":
"34b2f0679069792109c9d2323d788d19262e943a9672769f631536e750d7fd56", "srctyp": "E-Invoice", "pos": "33", "idt": "13-01-2024", "rchrg": "N", "irngendate": "13-01-2024", "inum": "CWPSI2324-09341", "chksum":
"1d7b0f2499677033e45a20bdd43fd53c85616f79da70e11ee9ae0b4f51bd8a8e"}, {"val": 14000, "itms": [{"num": 1, "itm_det": {"csamt": 0, "samt": 1067.76, "rt": 18, "txval": 11864, "camt": 1067.76, "iamt": 0}}], "inv_typ": "R", "irn":
"de1e12a4bf6404eedf979956598e04be33f66f63b0dabc776723486d98570dd5", "srctyp": "E-Invoice", "pos": "33", "idt": "18-01-2024", "rchrg": "N", "irngendate": "18-01-2024", "inum": "CWPSI2324-09410", "chksum":
"9e3b00963ea20211f263320f6261d9dbf5a3e5f839f4993047504f2b2758f76c"}, {"val": 14000, "itms": [{"num": 1, "itm_det": {"csamt": 0, "samt": 1067.76, "rt": 18, "txval": 11864, "camt": 1067.76, "iamt": 0}}], "inv_typ": "R", "irn":
"105cc757ed9c462ca6756127c972905136667042d0e0a03c261f73471c47e5c1", "srctyp": "E-Invoice", "pos": "33", "idt": "22-01-2024", "rchrg": "N", "irngendate": "22-01-2024", "inum": "CWPSI2324-09518", "chksum":
"61144d4c6dddfe80c7c501be238b625181c74e845c00bc07c6f4a37d13cd7050"}, {"val": 11200, "itms": [{"num": 1, "itm_det": {"csamt": 0, "samt": 854.21, "rt": 18, "txval": 9491.2, "camt": 854.21, "iamt": 0}}], "inv_typ": "R", "irn":
"6190d55cb74809ac32829a35cdd81c16109aa7d3645060d669e5b13fbb89855b", "srctyp": "E-Invoice", "pos": "33", "idt": "24-01-2024", "rchrg": "N", "irngendate": "24-01-2024", "inum": "CWPSI2324-09582", "chksum":
"4bf600b76a609d42769f343e40c2ceedde83d3c201100bd8a6a5c943190c3169"}, {"val": 2800, "itms": [{"num": 1, "itm_det": {"csamt": 0, "samt": 213.55, "rt": 18, "txval": 2372.8, "camt": 213.55, "iamt": 0}}], "inv_typ": "R", "irn":
"9db8e41e430c10824712f4a15aba2dd4bef850b79ba72621f96be0cc7ccf594d", "srctyp": "E-Invoice", "pos": "33", "idt": "29-01-2024", "rchrg": "N", "irngendate": "29-01-2024", "inum": "CWPSI2324-09703", "chksum":
"f28691668d85be8c90e5b86783fdb703c39f4ee97cff9445b74ed8eb155eff42"}, {"val": 14000, "itms": [{"num": 1, "itm_det": {"csamt": 0, "samt": 1067.76, "rt": 18, "txval": 11864, "camt": 1067.76, "iamt": 0}}], "inv_typ": "R", "irn":
"e0c309c8227c6ee777877c69f9cb98d9715f59758f2ea9ba22dd925e0f0a6056", "srctyp": "E-Invoice", "pos": "33", "idt": "31-01-2024", "rchrg": "N", "irngendate": "31-01-2024", "inum": "CWPSI2324-09772", "chksum":
"d975f3cbf522017cd9087b16bad4b9d74b5c2f42f6e0b609989e1fedea436c9d"}], "cfs": "Y", "ctin": "33AAECB7398D1ZN", "fldtr1": "09-Feb-24", "cfs3b": "N", "flprdr1": "Jan-24"}, {"inv": [{"val": 31735, "itms": [{"num": 1, "itm_det": {"csamt": 0,
"samt": 2968.7, "rt": 28, "txval": 21205, "camt": 2968.7}}, {"num": 2, "itm_det": {"csamt": 0, "samt": 350.28, "rt": 18, "txval": 3892, "camt": 350.28}}], "inv_typ": "R", "pos": "33", "idt": "01-01-2024", "rchrg": "N", "inum": "13376",
"chksum": "7598c63370364a85b633fa5ba8d9ee90230c1dbc254eb33253194a07022456c1"}, {"val": 20452, "itms": [{"num": 1, "itm_det": {"csamt": 0, "samt": 379.08, "rt": 18, "txval": 4212, "camt": 379.08}}, {"num": 2, "itm_det": {"csamt": 0, "samt":
1693.3, "rt": 28, "txval": 12095, "camt": 1693.3}}], "inv_typ": "R", "pos": "33", "idt": "01-01-2024", "rchrg": "N", "inum": "13429", "chksum": "ca2ab675289e07a7a50b7193795abb2f1237164a034ef96a2ee654c55c143105"}, {"val": 4767, "itms":
[{"num": 1, "itm_det": {"csamt": 0, "samt": 363.6, "rt": 18, "txval": 4040, "camt": 363.6}}], "inv_typ": "R", "pos": "33", "idt": "02-01-2024", "rchrg": "N", "inum": "13453", "chksum":
"eaf85d75465e0810de60078be8fdfe5c0c9f661a7bef373263e7fafea52f7289"}, {"val": 1161, "itms": [{"num": 1, "itm_det": {"csamt": 0, "samt": 88.56, "rt": 18, "txval": 984, "camt": 88.56}}], "inv_typ": "R", "pos": "33", "idt": "09-01-2024",
"rchrg": "N", "inum": "13526", "chksum": "e5c906fba4084774dffff3510b7544b272bbe1015d58fe60dd4d883824ff1819"}, {"val": 635, "itms": [{"num": 1, "itm_det": {"csamt": 0, "samt": 48.42, "rt": 18, "txval": 538, "camt": 48.42}}], "inv_typ": "R",
"pos": "33", "idt": "12-01-2024", "rchrg": "N", "inum": "13548", "chksum": "2c2d1e48f3e0bdcd2551410934adab8bc907c1dc22d350b37029ef84d685dd8b"}, {"val": 1335, "itms": [{"num": 1, "itm_det": {"csamt": 0, "samt": 79.56, "rt": 18, "txval": 884,
"camt": 79.56}}, {"num": 2, "itm_det": {"csamt": 0, "samt": 31.92, "rt": 28, "txval": 228, "camt": 31.92}}], "inv_typ": "R", "pos": "33", "idt": "12-01-2024", "rchrg": "N", "inum": "13554", "chksum":
"7be7796c81ae325bb73717ebd61ecd2225939bc3cab921a444543befa25062de"}, {"val": 13021, "itms": [{"num": 1, "itm_det": {"csamt": 0, "samt": 1424.22, "rt": 28, "txval": 10173, "camt": 1424.22}}], "inv_typ": "R", "pos": "33", "idt": "13-01-2024",
"rchrg": "N", "inum": "13555", "chksum": "5237e1006028b4d3a5de644e6f7af7dec09a111ae3b5b7c4fa5d0032007bcd3e"}, {"val": 208, "itms": [{"num": 1, "itm_det": {"csamt": 0, "samt": 15.84, "rt": 18, "txval": 176, "camt": 15.84}}], "inv_typ": "R",
"pos": "33", "idt": "13-01-2024", "rchrg": "N", "inum": "13558", "chksum": "c5df22a52190830d3fa8d496b751503ba6649fa7b8b7d1e1b386564b903a18f3"}, {"val": 130, "itms": [{"num": 1, "itm_det": {"csamt": 0, "samt": 9.9, "rt": 18, "txval": 110,
"camt": 9.9}}], "inv_typ": "R", "pos": "33", "idt": "20-01-2024", "rchrg": "N", "inum": "13589", "chksum": "2274b91871008718499c902f0d2890926ed22b9bbd6f922a12ab220ab689ea2d"}, {"val": 467, "itms": [{"num": 1, "itm_det": {"csamt": 0, "samt":
51.1, "rt": 28, "txval": 365, "camt": 51.1}}], "inv_typ": "R", "pos": "33", "idt": "23-01-2024", "rchrg": "N", "inum": "13627", "chksum": "57cc5e68b13e868754883f3bd5d8c928695c21dc6a9b4864b15c7473c7b7bb67"}, {"val": 393, "itms": [{"num": 1,
"itm_det": {"csamt": 0, "samt": 29.97, "rt": 18, "txval": 333, "camt": 29.97}}], "inv_typ": "R", "pos": "33", "idt": "31-01-2024", "rchrg": "N", "inum": "13657", "chksum":
"ce2eba7c31778af44d99c1154b7b07649fd2af8aab255bc4d5f461311827fa80"}], "cfs": "N", "ctin": "33AAQFT1511R1ZR", "cfs3b": "N", "flprdr1": "Jan-24"}]
    print(len(gst_data))
    return gst_data
    gst_integration_settings = frappe.get_single('GST Integration Settings')

    # GST integration Details
    user_name = gst_integration_settings.user_name
    base_url = gst_integration_settings.base_url
    content_type = gst_integration_settings.content_type

    otp = gst_integration_settings.otp
    requestid = random_string(randint(8, 16))
    gstin = None
    if gstin:
        state_code = gstin[:2]
    else:
        gstin = gst_integration_settings.gstin
        state_code = gstin[:2]

    ret_period = getdate(filters.get("to_date")).strftime("%m%Y")

    if not all([user_name, base_url, content_type, requestid, gstin, ret_period]):
        frappe.throw("GST Details Missing")

    access_token = get_access_token(gst_integration_settings, base_url)

    path = "/enriched/returns/gstr2a"
    if gst_integration_settings.is_testing:
        path = "/test/enriched/returns/gstr2a"

    url = base_url + path

    params = {
        "action": cstr(action).upper(),
        "gstin": gstin,
        "ret_period": ret_period
    }

    headers = {
            'username':  user_name,
              'state-cd': state_code,
              'otp': otp,
              'Content-Type': content_type,
              'requestid': requestid,
              'gstin': gstin,
              'ret_period': ret_period,
              'Authorization': "Bearer " + access_token
        }

    response = requests.request(
        "GET", url, params=params, headers=headers )

    create_api_log(response, action="GSTR2 " + action)

    if response.ok:
        res = response.json()
        if res.get('status') == 200:
            return res.get(action.lower())
        else:
            frappe.throw(res.get('message'), title="BAD Response")
    else:
        frappe.throw("{}".format(response), title= "Api Error")



