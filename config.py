# -*- coding: utf-8 -*-
import os, uuid
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # flask_login
    USE_SESSION_FOR_NEXT = False  # 去除请求中next参数
    SESSION_PROTECTION = 'strong'
    REMEMBER_COOKIE_DURATION = timedelta(days=1)

    # session过期时间
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    # 文件上传控制
    UPLOAD_PATH = os.path.join(basedir, 'app/static/upload')
    UPLOAD_MAX_SIZE = 1024 * 1024 * 200  # 200MB
    UPLOAD_ALLOWED_EXTENSIONS = ['apk', 'jpg', 'png', 'gif', 'csv', 'txt']

    SECRET_KEY = os.environ.get('SECRET_KEY') or str(uuid.uuid1())
    WTF_CSRF_ENABLED = False
    # 下面参数必需为真,否则有些地方请求结束后不提交数据库会有问题.
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    # token过期时长，单位秒
    HAPYAK_JWT_LIFETIME = 24 * 60 * 60
    # 生成token加密秘钥
    JWT_KEY = 'SD2asdf2'
    GEOIP_FILEPATH = 'basefunc/geoip.dat'
    GEOIP_CACHE = 'MEMORY_CACHE'
    LOG_QUE_NAME = 'logque'
    
    # Boss 全局配置
    # vod2 的ip用来作为7.0启动界面获取资源接口ip
    # vod 的ip用来作为主界面加载信息的接口，没有的话，会弹框无法获得信息。。。。
    # api 的ip用来作为盒子，app等获取相关接口的入口ip
    BOSS_CONFIG = {"area_str": "",
                   "splash_url": "http://221.228.74.41/suntvres/image/STB_SPLASH_IMG.png",
                   "bg_img_url": "http://221.228.74.41/suntvres/image/STB_BG_IMG.png",
                   "stream_update_code": 1001,
                   "channel_video_type": {"iphone": {"code": "iphone", "value": 256000, "lable": "音频"},
                                          "ipad": {"code": "ipad", "value": 512000, "lable": "流畅"},
                                          "iptv": {"code": "iptv", "value": 800000, "lable": "标清"},
                                          "ipsd": {"code": "ipsd", "value": 1500000, "lable": "高清"},
                                          "ipxd": {"code": "ipxd", "value": 3000000, "lable": "超清1"},
                                          "iped": {"code": "iped", "value": 4000000, "lable": "超清2"},
                                          "iphd": {"code": "iphd", "value": 7500000, "lable": "超清3"}},
                   "domain": [{"res_s_code": "Global", "res_s_name": "全球服务", "api": "192.168.78.41", "vod": "221.228.74.41",
                               "vod2": "69.169.34.24", "live": "192.168.78.41", "search": "221.228.74.41", "log": "192.168.78.41",
                               "ads": "69.169.34.24"}]
                   }

    # 低级版本盒子的升级配置项
    STB_CONFIG = {"QA2": "http://dispatch.suntv.tv/static/upload/QA20.4.91.apk?v=3.0",
                  "ASF": "http://dispatch.suntv.tv/static/upload/ASF0.5.32.apk?v=5.0"
                  }

    # YouTube插件下载地址
    YOUTB = {
        "mtl": {"url": "http://dispatch.suntv.tv/static/upload/YouTube5.5.27.apk", "md5": "a5d72785c39ea9ee66d529616baa9786", "size": 8374746},
        "phd": {"url": "http://dispatch.suntv.tv/static/upload/YouTube12.16.56.apk", "md5": "51d03293a50664c4c7805dfc2e242239",
                "size": 21504340}
    }

    # apk安装包白名单
    APK_WHITELIST = {"count": 249,
                     "list":
                         ["com.tvm.suntv.news.client.activity", "com.netflix.mediaclient", "com.hulu.plus",
                         "com.sling.international", "com.hbo.go", "com.hbo.hbonow", "com.dailymotion.dailymotion",
                         "com.moretv.android", "com.elinkway.tvlive2", "com.molitv.android", "cn.kuwo.sing.tv",
                         "tv.icntv.migu", "cn.wps.moffice_i18n_TV", "com.ted.android", "com.duolingo",
                         "com.accuweather.android", "com.onemainstream.cbsnews.android", "com.foxnews.foxnewselection",
                         "com.nbcsports.news", "com.dangbei.zhushou", "tv.fun.master", "com.cmcm.cleanmaster.tv",
                         "com.ucbrowser.tv", "cn.etouch.ecalendarTv", "com.dianshiyouhua", "com.gitvdemo.video",
                         "com.pplive.androidxl", "cn.cibntv.ott", "cn.com.wasu.main", "tv.danmaku.bili", "com.fyzb.tv",
                         "cn.beevideo", "com.douyu.xl.douyutv", "com.duowan.kiwitv", "com.tencent.qqmusictv",
                         "com.kugou.playerHD", "cn.kuwo.kwmusichd", "com.duomi.androidtv", "com.baidu.music.pad",
                         "com.kgeking.client", "com.multak.LoudSpeakerKaraoke", "air.SkymediaKTV", "com.kandian.mv4tv",
                         "com.trans.pvz", "com.bf.sgs.hdexp", "com.bf.GuoBiaoHD", "com.bf.ERShuangKou",
                         "com.trans.othello", "com.polarbit.ragingthunder", "com.sxiaoao.car3d2",
                         "org.cocos2dx.FishingJoy2", "Com.Coocaa.AhZk.EsYd", "Com.Coocaa.AhZk.Sl",
                         "com.boyaa.lordland.tv", "com.iflyor.binfuntv", "com.dianlv.tv", "com.tv.topnews",
                         "tvm.yidian.suntv", "com.tvm.tcl.home", "com.ctbri.youxt.tvbox", "com.xunlei.kankan.tv",
                         "org.validate.steven", "com.c38.iptv1", "com.tvm.suntv.home", "tvm.hdtv.suntv",
                         "com.vcinema.client.tv", "com.panodic.factest", "newsclient.tvm.com.mynewsclient",
                         "com.iptv.hdkan", "com.golive.tc", "com.hdtv", "com.tcl.launcher", "com.test.player",
                         "com.tvm.cloud", "com.gwtv.cn.tv.pad", "com.duonao.player", "com.hunantv.imgo.activity",
                         "com.starcor.mango", "com.google.android.youtube.tv", "com.viki.android", "com.ted.android.tv",
                         "com.spotify.music", "com.nousguide.android.rbtv", "com.mubi", "com.haystack.android",
                         "com.crackle.androidtv", "com.attendify.conftoayzl", "com.bonkotv.android.bonkotv",
                         "org.xbmc.kodi", "com.primetimeservice.primetime.tv", "com.booslink.Wihome_videoplayer3",
                         "com.tlmp", "com.tlmv", "com.changba", "com.cloud.tv", "com.giec.gitv", "com.thunder.tv",
                         "com.iflytek.aichang.tv", "com.tencent.karaoke", "com.famousbluemedia.yokeeS",
                         "com.bobo.splayer", "tv.wan8.weisp", "com.wole.android.pad.client", "net.myvst.v2",
                         "tv.huan.le.live", "com.bit.tvlive.activity", "tv.danmaku.bilixl", "cn.cibn.chan", "cn.cntvhd",
                         "cn.cntvnews.tv", "cn.pipi.mobile.pipiplayer.hd", "com.android.t1.onlinetv",
                         "com.androidx.live", "com.bigertv.launcher", "com.cibn.tv", "com.controller.tv",
                         "com.dluxtv.shafamovie", "com.doule.video", "com.eagle.live", "com.elinkway.tvlive",
                         "com.estream.tv", "com.example.lanmeiiptv", "com.example.ttsupertv", "com.exp.tv.sstar",
                         "com.fanshi.tvvideo", "com.fun.tv", "com.funshion.integrator.pad", "com.funshion.video.pad",
                         "com.gameabc.zhanqiAndroidTv", "com.gemini.bbtv", "com.gitv.tv.cinema", "com.golive.cinema",
                         "com.guibao.tv.talkshow", "com.guibao.tv.vmovie", "com.guibao.tv.wwmxd",
                         "com.haowang.xiangkantv", "com.hooray.snm", "com.hpkj.yzcj_tv", "com.hupu.games",
                         "com.hyh.live", "com.js.litchi", "com.kaiboer.huibo", "com.kaiboer.veryhighvideo",
                         "com.kaiboertvlive.activity", "com.kandian.vodapp4tv", "com.kascend.tvassistant",
                         "com.ktcp.video", "com.kuaishuo.tv", "com.kuyun.kutv", "com.letv.leso", "com.letv.tv",
                         "com.live.livetv", "com.live.xiguaa", "com.lovetv.lxlive", "com.lovetv.mglive",
                         "com.maxway.maxtv2", "com.megaweb.tv", "com.maxway.maxtvplayback",
                         "com.michaellancy.lancyplayer.v3.apache", "com.mtday.bambiplayer.tv", "com.mylove.bslive",
                         "com.mylove.live", "com.mywa.tv", "com.noname.livetv", "com.nothingkill.wisplive",
                         "com.ott.qingsi.live", "com.panda.videolivetv", "com.pptv.tvsports", "com.qianxun.tvbox",
                         "com.qsp.launcher", "com.sanbuapp.niunan_3", "com.sanbuapp.niunan1", "com.sanbuapp.pangzhetv1",
                         "com.shapps.mintubeapp", "com.shenma.tvlauncher", "com.smit.livevideo", "com.sohuott.tv.vod",
                         "com.togic.livevideo", "com.tudou.tv.c", "com.tvlive.vodapp4tvlive",
                         "com.unionman.basketball_world", "com.vcinema.client.tv.cibn", "com.videoshelf", "com.vodhome",
                         "com.weibao.duoduoTV", "com.wepower.vod", "com.xiaojie.tv", "com.yc.tv", "com.youku.tv.c",
                         "com.yueti.livetv", "com.zbmv", "com.gameabc.esportsgo", "com.sanbuapp.victor1",
                         "com.moretv.comic", "com.targetv.live.tv", "gv.cloudtvbox", "hdp.li.fans", "org.stormrage",
                         "org.jykds.player", "org.keke.player", "qingjiaolive.com", "com.sanbuapp.cuitao_6",
                         "tv.le123.com.dianxin", "tv.wobo.movie", "com.cpsoft.youjiao.cc01", "com.estrongs.android.pop",
                         "com.moliplayer.android.tv", "com.example.Code_Test", "com.ott.maibo", "cn.cibntv.ott.test",
                         "com.example.androidtest", "tvm.yidian.suntvs", "com.google.android.gms",
                         "com.google.android.youtube", "cn.dolit.enlighten", "tv.suntv.box", "tv.suntv.enterprise",
                         "com.sz.ead.app.vbox", "com.letv.epg.activity", "cn.bangtv.ott", "com.tvm.suntv.maibo",
                         "cn.tvapp88888888.dnvod", "jackpal.androidterm", "com.youku.tv", "com.dangbeimarket",
                         "com.pbs.video", "tvm.changcheng.mbox", "hdpfans.com", "com.vst.live", "tg.zhibodi.browser2",
                         "com.iptv.hdkan", "com.duonao.player", "com.gochinatv.enlighten",
                         "com.dropbox.android-24.2.2-APK4Fun.com.apk", "com.dropbox.android", "com.android.vending",
                         "tv.suntv.youtube", "com.tvmining.mbtv", "com.hejunlin.liveplayback", "com.drwang.edu",
                         "com.wayatv.com", "com.youpeng.tv", "com.favback", "cy.flash.mediabox",
                         "com.wayatv.android.box", "com.conch.itv", "com.ez.ead.app.vboxfull2_tvchina", "com.tv.tyzb",
                         "com.ty.tyzb"]
                    }

    IP_SEARCH_URL = "http://115.159.144.132/ip/ipsearch?ipstr="

    # redis中产品包与频道关系保存key
    REDIS_PRODUCT_CHANNEL_KEY = "product_channels"
    # redis中节点与频道关系保存key
    REDIS_NODE_CHANNEL_KEY = "node_channels"

    # 下面这个为空置的话，使用ip访问会地址404
    # SERVER_NAME = '192.168.78.144'

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql://suntv:SunTV@123456@10.0.70.11/suntv'
    SQLALCHEMY_ECHO = True
    REDIS0_URL = "redis://:123456@10.0.70.11:6379/0"
    REDIS1_URL = "redis://:123456@10.0.70.11:6379/1"


class TestConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql://suntv:SunTV@123456@10.0.70.11/suntv'
    SQLALCHEMY_ECHO = True
    REDIS0_URL = "redis://:123456@10.0.70.11:6379/0"
    REDIS1_URL = "redis://:123456@10.0.70.11:6379/1"


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql://suntv:SunTV@123456@10.0.70.11/suntv'
    REDIS0_URL = "redis://:123456@10.0.70.11:6379/0"
    REDIS1_URL = "redis://:123456@10.0.70.11:6379/1"

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'test': TestConfig,
    'default': ProductionConfig
}
