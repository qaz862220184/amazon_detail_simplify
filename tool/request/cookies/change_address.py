# -*- coding: UTF-8 -*-
import asyncio
from tool.request.validate.captcha import ValidateCaptcha
from pyppeteer import launch
import pyppeteer.errors
from fake_useragent import UserAgent

ua = UserAgent(min_percentage=2.1)


class AmazonLocationSession(object):

    def __init__(self, domain: str, zip_code: str, language, chrome_executable_path, proxies=None):
        self.domain = domain
        self.zip_code = zip_code
        self.language = language
        self.chrome_executable_path = chrome_executable_path
        self.proxies = proxies
        base_url = self.get_base_url()
        self.base_url = base_url

    async def scrapy_browser(self):
        """
        创建浏览器对象
        :return:
        """
        scrapy_browser = await launch({
            'executablePath': self.chrome_executable_path,
            'headless': False,
            'autoClose': True,
            'dumpio': True,
            'ignoreDefaultArgs': ['--enable-automation'],
            "args": [
                '--start-maximized',
                '--disable-infobars',
                '--disable-extensions',
                '--disable-web-security',
                '--lang=en-US',
                '--no-sandbox',
                '--blink-settings=imagesEnabled=false',  # 禁止加载图片
                '--user-agent={}'.format(ua.chrome),
                '--proxy-server={}'.format(self.proxies),
            ]
        })
        return scrapy_browser

    async def get_page(self, browser):
        page = await browser.newPage()
        await page.setViewport({  # 最大化窗口
            "width": 1920,
            "height": 1040,
            'deviceScaleFactor': 3.0,
            'isMobile': True,
            'hasTouch': True
        })
        await page.evaluateOnNewDocument("""() => {
                                    Object.defineProperty(navigator, webdriver, { get: () => false })
                                }""")
        page.setDefaultNavigationTimeout(0)

        return page

    def change_address(self):
        """
        选择地址
        :return:
        """
        loop = asyncio.get_event_loop()
        page_cookies = loop.run_until_complete(self._change_address())
        return page_cookies

    async def _change_address(self):
        browser = await self.scrapy_browser()
        page = await self.get_page(browser=browser)
        await page.goto(self.base_url, {'waitUntil': 'domcontentloaded'})
        # 验证码
        html = await page.content()
        # await page.waitFor(1000*60)
        # 识别验证码
        if ValidateCaptcha.is_verification(html):
            # 验证验证码
            await self.__verification(
                html=html,
                browser=page
            )
        # 欧洲站的记住cookie
        try:
            await page.waitFor(3 * 1000)
            await page.click('#sp-cc-accept')
            await page.waitFor(3 * 1000)
        except:
            pass
        # 接下来是选择地址的操作
        # 地址选择有可能没有出现重新刷新一遍
        try:
            await page.waitForSelector('#nav-global-location-popover-link', timeout=5*1000)
        except pyppeteer.errors.TimeoutError:
            await page.reload()
            await page.waitFor(3*1000)
        await page.click('#nav-global-location-popover-link')
        # 检查地址选择弹窗
        for i in range(3):
            try:
                await page.waitForSelector('#GLUXSpecifyLocationDiv', timeout=10*1000)
                break
            except pyppeteer.errors.TimeoutError:
                await page.click('#nav-global-location-popover-link')
        # 输入邮编
        js_code = '()=>{' + await self.__get_input_js_code(browser=page) + '}'
        await page.evaluate("""{}""".format(js_code))
        await page.waitFor(3*1000)
        await page.click('#GLUXZipUpdate')
        # 结束
        try:
            await page.waitFor(2*1000)
            await page.waitForSelector('#GLUXConfirmClose-announce', timeout=5 * 1000)
            await page.click('#GLUXConfirmClose')
        except:
            await page.waitFor(3*1000)

        await page.reload()
        # 获取cookie
        cookies = await page.cookies()
        return cookies

    async def __verification(self, html, browser):
        """
        验证验证码
        :param html:
        :return:
        """
        validate = ValidateCaptcha(
            html,
            self.base_url,
        )
        amazon_code = validate.get_amazon_code()
        # 输入验证码
        await browser.type('#captchacharacters', amazon_code)
        await asyncio.wait([
            browser.waitForNavigation({'waitUntil': 'domcontentloaded'}),
            browser.click('body > div > div.a-row.a-spacing-double-large > div.a-section > div > div > form > div.a-section.a-spacing-extra-large > div > span > span > button'),
        ])

    async def __get_input_js_code(self, browser):
        """
        获取输入的js代码
        :param browser:
        :return:
        """
        if await browser.xpath('//*[@id="GLUXZipUpdateInput_0"]'):
            is_cut = True
        else:
            is_cut = False
        if is_cut is True:
            # 多个input框
            if '-' in self.zip_code:
                zip_code_arr = self.zip_code.split('-')
            else:
                zip_code_arr = self.zip_code.split(' ')
            one, two = zip_code_arr
            js_code = f"document.getElementById('GLUXZipUpdateInput_0').value='{one}';" \
                      f"document.getElementById('GLUXZipUpdateInput_1').value='{two}';"
        else:
            js_code = f"document.getElementById('GLUXZipUpdateInput').value='{self.zip_code}';"
        return js_code

    def get_base_url(self):
        """
        获取基础链接
        :return:
        """
        language = '?language={}'.format(self.language) if self.language else ''
        if '://' in self.domain:
            return self.domain + language
        else:
            return 'https://' + self.domain + language


if __name__ == '__main__':
    # TODO nl,au,ae,sa,eg无法输入邮编
    amazon = AmazonLocationSession('www.amazon.com', '10002', 'en-us', 'C:/Program Files/Google/Chrome/Application/chrome.exe', 'http://192.168.2.84:7102')
    cookies = amazon.change_address()
    print(cookies)
