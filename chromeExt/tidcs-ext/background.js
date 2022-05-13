function request(option, callback) {
    let xhr = new XMLHttpRequest()
    xhr.open(option.method, option.url)
    if (option.headers) {
        for (let key in option.headers) {
            xhr.setRequestHeader(key, option.headers[key])
        }
    }
    // 设置完成回调
    xhr.onreadystatechange = function () {
        // In local files, status is 0 upon success in Mozilla Firefox
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 403) {
                tiAutoLogin()
            }
            callback ? callback(xhr) : null
        }
    };
    option.body ? xhr.send(option.body) : xhr.send()
}


/*
* 1.插件加载则尝试与后台服务简历SocketIo连接, 监听来自后台服务的任务数据
*/

// https://developer.chrome.com/docs/extensions/reference/runtime/#property-id 
const myExtensionId = chrome.runtime.id;
const tiOrigin = "www.ti.com.cn"
const TiAddtoCartSource = "ti.com-productfolder"
// const BackendSrvAddr = 'ws://127.0.0.1:43998';
const BackendSrvAddr = 'ws://175.178.246.168';
let TiAutoLoginIng = false;
let TiGetProfileClock = null;
let TiKeepStatusClock = null;

console.debug("ExtensionId: " + myExtensionId);

let SocketIoCli = io(BackendSrvAddr, {
    autoConnect: true,
    transports: ["websocket", "polling"],
});

SocketIoCli.on("connect", function () {
    let email = localStorage.getItem("email")
    let password = localStorage.getItem("password")
    if (!email || !password) {
        console.log("未保存登录邮箱或密码")
        SocketIoCli.emit("auto_login_fail", {errmsg: "未保存登录邮箱或密码"})
        return false
    }
    tiProfile()
    // tiCart()
    if (TiGetProfileClock) {
        clearInterval(TiGetProfileClock)
    }
    TiGetProfileClock = setInterval(tiProfile, 1000 * 60) // 每分钟检查一次登录状态
    if (TiKeepStatusClock) {
        clearInterval(TiKeepStatusClock)
    }
    TiKeepStatusClock = setInterval(tiKeepStatus, 1000 * 60 * 5) // 每5分钟检测一次购物车token状态
})

SocketIoCli.on("error", function (error) {
    console.log(error)
})

SocketIoCli.on("ping", function () {
    SocketIoCli.emit("pong")
})

SocketIoCli.on("spider_product_base", function (params) {
    tiProductBase(params.code)
})

SocketIoCli.on("spider_product_ivt", function (params) {
    tiProductIvt(params.codes)
})

SocketIoCli.on("spider_cart", function () {
    tiCart()
})

SocketIoCli.on("ti_add_product2cart", function (params) {
    tiAddProduct2Cart(params)
})


// 监听来自插件其他组成部分的消息
chrome.runtime.onMessage.addListener(
    /* https://developer.chrome.com/docs/extensions/reference/runtime/#event-onMessage
     * Notice: 'message.recipient' is self-defined
     */
    function (message, sender, sendResponse) {
        if (sender.id === myExtensionId && message.recipient === 'background') {
            switch (message.action) {
                case "tiAutoLogin": // 自动登录完成的回调
                    TiAutoLoginIng = false
                    if (message.errmsg) {
                        SocketIoCli.emit("auto_login_fail", {errmsg: message.errmsg})
                    } else {
                        tiProfile()
                    }
                    break;
            }
            sendResponse({})
        }
    }
);

// 修改从本插件发起任务请求的请求头信息, 防止被跨域限制
chrome.webRequest.onBeforeSendHeaders.addListener(
    function (detail) {
        let headers = detail.requestHeaders;
        if (detail.initiator === "chrome-extension://" + chrome.runtime.id) {
            let origin = detail.url.match(/(http(s)?:\/\/.*?)\/.*/)[1]
            headers.map((item) => {
                if (item.name === "Origin") {
                    item.value = origin;
                }
                if (item.name === "Sec-Fetch-Site") {
                    item.value = "same-origin"
                }
            })
            headers.push({
                name: "Referer",
                value: origin
            })
        }
        return {
            requestHeaders: headers
        }
    }, {
        urls: ["<all_urls>"]
    },
    ["blocking", "requestHeaders", "extraHeaders"],
)


// 点击插件图标打开一个自定义页面
chrome.browserAction.onClicked.addListener(function () {
    let centerURL = chrome.extension.getURL('background.html');
    chrome.tabs.query({
        'url': centerURL
    }, function (tabs) {
        if (tabs.length > 0) {
            chrome.tabs.update(tabs[0].id, {
                'active': true
            });
            for (let i = 1; i < tabs.length; i++) {
                chrome.tabs.remove(tabs[i].id);
            }
        } else {
            chrome.tabs.create({
                'url': centerURL,
            });
        }
    })
});

function workerOnline(tiProfileData) {
    TiAutoLoginIng = false
    tiProfileData.email = localStorage.getItem("email")
    SocketIoCli.emit("worker_online", {
        email: localStorage.getItem('email'),
        company_name: tiProfileData.companyProfile
    })
}

function workerOffline() {
    SocketIoCli.emit("worker_offline", {
        email: localStorage.getItem('email'),
    })
}

window.tiProfile = tiProfile

function tiProfile() {
    if (TiAutoLoginIng) {
        return false
    }
    let option = {
        method: "GET",
        url: `https://${tiOrigin}/avlmodel/api/user/info?locale=zh-CN`,
    }
    request(option, function (xhr) {
        if (xhr.status !== 200) {
            console.log(`${tiOrigin}服务器异常，返回状态码${xhr.status}`)
            return false
        }
        if (xhr.responseURL.indexOf('login.ti.com') > -1) {
            // 未登录，则开启登录任务
            workerOffline()
            tiAutoLogin()
        } else {
            let tiProfileData = JSON.parse(xhr.responseText)
            workerOnline(tiProfileData)
            // tiCart() // 更新购物车
        }
    })
}

window.tiCart = tiCart

function tiCart() {
    if (TiAutoLoginIng) {
        return false
    }
    let option = {
        method: "GET",
        url: `https://${tiOrigin}/occservices/v2/ti/viewCart?currency=CNY`
    }
    request(option, function (xhr) {
        if (xhr.status !== 200) {
            console.log(`${tiOrigin}服务器异常，返回状态码${xhr.status}`)
            return false
        }
        if (xhr.responseURL.indexOf('login.ti.com') > -1) {
            // 未登录，则开启登录任务
            workerOffline()
            tiAutoLogin()
        } else {
            let tiCartData = JSON.parse(xhr.responseText)
            SocketIoCli.emit("update_cart", tiCartData)
        }
    })

}

window.tiProductBase = tiProductBase

function tiProductBase(code) {
    if (TiAutoLoginIng) {
        return false
    }
    let option = {
        method: "GET",
        url: `https://${tiOrigin}/avlmodel/api/singlepart?searchTerm=${code}&operation=page-load&locale=zh-CN`
    }
    request(option, function (xhr) {
        if (xhr.status !== 200) {
            console.log(`${tiOrigin}服务器异常，返回状态码${xhr.status}`)
            return false
        }
        if (xhr.responseURL.indexOf('login.ti.com') > -1) {
            // 未登录，则开启登录任务
            workerOffline()
            tiAutoLogin()
        } else {
            let searchRes = JSON.parse(xhr.responseText)
            let matchedProduct = {
                orderablePartNumber: code,
                partDescription: "未抓取到数据，请检查型号是否正确",
                price: {
                    basePrice: null,
                    currencyCode: null,
                    baseQty: null,
                },
                orderLimit: null
            }
            if (searchRes.tempCounts > 0) {
                let tiOpnList = searchRes.result.matches.tiOpnList
                for (let i = 0; i < tiOpnList.length; i++) {
                    let item = tiOpnList[i];
                    if (item.orderablePartNumber === code) {
                        matchedProduct = item
                        break
                    }
                }
            }
            SocketIoCli.emit("update_product_base", matchedProduct)
        }
    })
}

window.tiProductIvt = tiProductIvt

function tiProductIvt(codes) {
    if (TiAutoLoginIng) {
        return false
    }
    let option = {
        method: "POST",
        url: `https://${tiOrigin}/avlmodel/api/inv-stock-forecast-info?locale=zh-CN`,
        headers: {"content-type": "application/json"},
        body: JSON.stringify(codes),
    }
    request(option, (xhr) => {
        if (xhr.status !== 200) {
            console.log(`${tiOrigin}服务器异常，返回状态码${xhr.status}`)
            return false
        }
        if (xhr.responseURL.indexOf('login.ti.com') > -1) {
            // 未登录，则开启登录任务
            workerOffline()
            tiAutoLogin()
        } else {
            let ivtRes = JSON.parse(xhr.responseText)
            SocketIoCli.emit("update_product_ivt", ivtRes)
        }
    })
}

window.tiAddProduct2Cart = tiAddProduct2Cart

function tiAddProduct2Cart(params) {
    if (TiAutoLoginIng) {
        return false
    }
    // 先获取购物车的最新信息
    let option = {
        method: "GET",
        url: `https://${tiOrigin}/occservices/v2/ti/viewCart?currency=CNY`
    }
    request(option, function (xhr) {
        if (xhr.status !== 200) {
            console.log(`${tiOrigin}服务器异常，返回状态码${xhr.status}`)
            return false
        }
        if (xhr.responseURL.indexOf('login.ti.com') > -1) {
            // 未登录，则开启登录任务
            workerOffline()
            tiAutoLogin()
        } else {
            let tiCartData = JSON.parse(xhr.responseText)
            SocketIoCli.emit("update_cart", tiCartData)
            //
            let canAdd = true
            if (tiCartData.Items) { // 如果购物车存在产品，则需要检测是否是重复加购物车
                for (let i = 0; i < tiCartData.Items.length; i++) {
                    let item = tiCartData.Items[i]
                    if (item.OpnId === params.code) {
                        canAdd = false
                        console.log("跳过重复加购物的操作")
                        break
                    }
                }
            }
            if (canAdd) {
                request(
                    {
                        method: "POST",
                        url: `https://${tiOrigin}/occservices/v2/ti/addtocart`,
                        headers: {"content-type": "application/json"},
                        body: JSON.stringify({
                            cartRequestList: [
                                {
                                    packageOption: null,
                                    opnId: params.code,
                                    quantity: params.quantity,
                                    tiAddtoCartSource: TiAddtoCartSource,
                                    sparam: ""
                                }
                            ],
                            currency: params.currency
                        })
                    },
                    (xhr) => {
                        if (xhr.status !== 200) {
                            console.log(`${tiOrigin}服务器异常，返回状态码${xhr.status}`)
                            return false
                        }
                        if (xhr.responseURL.indexOf('login.ti.com') > -1) {
                            // 未登录，则开启登录任务
                            workerOffline()
                            tiAutoLogin()
                        } else {
                            let addCartRes = JSON.parse(xhr.responseText)
                            if (addCartRes.statusCode === "200") {
                                SocketIoCli.emit("add_product2cart_ok", params)
                            }
                        }
                    }
                )
            }
        }
    })
}

function openTiLoginPage(tabId) {
    chrome.tabs.update(tabId,
        {url: `https://${tiOrigin}/secure-link-forward/?gotoUrl=https://${tiOrigin}`},
        () => {
            // 设置定时任务监听tab的加载状态，记载完成后再进行下一步
            let tabStatusClock = setInterval(function () {
                console.log("openTiLoginPage check tab status")
                chrome.tabs.get(tabId, function (tab) {
                    if (tab.status === "complete") {
                        clearInterval(tabStatusClock);
                        if (tab.url.startsWith("https://login.ti.com")) {
                            let email = localStorage.getItem("email")
                            let password = localStorage.getItem("password")
                            if (!email || !password) {
                                console.log("未保存登录邮箱或密码")
                                return false
                            }
                            chrome.tabs.sendMessage(tabId, {
                                recipient: 'content',
                                task: {
                                    cmd: "tiLogin",
                                    email: email,
                                    password: password
                                }
                            })
                        }
                    }
                })
            }, 2000)
        })
}

window.tiAutoLogin = tiAutoLogin

function tiAutoLogin() {
    if (TiAutoLoginIng) {
        return false
    }
    // 获取当前所有的tab
    TiAutoLoginIng = true;
    setTimeout(() => {
        TiAutoLoginIng = false // 自动登录的超时时间为2
    }, 1000 * 60 * 2)
    chrome.tabs.query({}, (tabs) => {
        let workTab = null
        for (let i = 0; i < tabs.length; i++) {
            if (tabs[i].url.indexOf('chrome-extension') === -1) {
                workTab = tabs[i]
                break
            }
        }
        if (workTab) {
            if (workTab.url.indexOf(tiOrigin) > -1) {
                chrome.tabs.reload(workTab.id, {bypassCache: true}, () => {
                    // 设置定时任务监听tab的加载状态，记载完成后再进行下一步
                    let tabStatusClock = setInterval(function () {
                        console.log("check tab status")
                        chrome.tabs.get(workTab.id, function (tab) {
                            if (tab.status === "complete") {
                                clearInterval(tabStatusClock);
                                openTiLoginPage(workTab.id)
                            }
                        })
                    }, 2000)
                })
            } else {
                chrome.tabs.update(workTab.id, {url: `https://${tiOrigin}`}, () => {
                    // 设置定时任务监听tab的加载状态，记载完成后再进行下一步
                    let tabStatusClock = setInterval(function () {
                        console.log("check tab status")
                        chrome.tabs.get(workTab.id, function (tab) {
                            if (tab.status === "complete") {
                                clearInterval(tabStatusClock);
                                openTiLoginPage(workTab.id)
                            }
                        })
                    }, 2000)
                })
            }
        } else {
            chrome.tabs.create({active: false, url: `https://${tiOrigin}`}, (tab) => {
                // 设置定时任务监听tab的加载状态，记载完成后再进行下一步
                let tabStatusClock = setInterval(function () {
                    console.log("check tab status")
                    chrome.tabs.get(tab.id, function (tab) {
                        if (tab.status === "complete") {
                            clearInterval(tabStatusClock);
                            openTiLoginPage(tab.id)
                        }
                    })
                }, 2000)
            })
        }
    })
}

function tiLogin() {
    if (TiAutoLoginIng) {
        alert(`程序正在尝试自动登录${tiOrigin}，请稍后再操作`)
        return false
    }
    let email = document.getElementById('email').value
    let password = document.getElementById('password').value
    if (!email || !password) {
        alert(`请完整填写${tiOrigin}登录邮箱与密码`)
        return false
    }
    console.log("tiLogin")
    let option = {
        method: "GET",
        url: `https://${tiOrigin}/avlmodel/api/user/info?locale=zh-CN`,
    }
    request(option, function (xhr) {
        if (xhr.status !== 200) {
            alert(`${tiOrigin}服务器异常，返回状态码${xhr.status}`)
            return false
        }
        if (xhr.responseURL.indexOf('login.ti.com') > -1) {
            // 未登录，则开启登录任务
            localStorage.setItem("email", email)
            localStorage.setItem("password", password)
            workerOffline()
            tiAutoLogin()
        } else {
            alert("当前存在已登录信息，请先手动退出登录后再尝试此功能")
            let tiProfileData = JSON.parse(xhr.responseText)
            workerOnline(tiProfileData)
            return false
        }
    })
}

function openTiCartPage(tabId) {
    chrome.tabs.update(tabId,
        {url: `https://${tiOrigin}/store/ti/en/cart`},
        () => {
            // 设置定时任务监听tab的加载状态，记载完成后再进行下一步
            let tabStatusClock = setInterval(function () {
                console.log("openTiCartPage check tab status")
                chrome.tabs.get(tabId, function (tab) {
                    if (tab.status === "complete") {
                        clearInterval(tabStatusClock);
                        if (tab.url.startsWith("https://login.ti.com")) {
                            let email = localStorage.getItem("email")
                            let password = localStorage.getItem("password")
                            if (!email || !password) {
                                console.log("未保存登录邮箱或密码")
                                return false
                            }
                            chrome.tabs.sendMessage(tabId, {
                                recipient: 'content',
                                task: {
                                    cmd: "tiLogin",
                                    email: email,
                                    password: password
                                }
                            })
                        }
                    }
                })
            }, 2000)
        })
}

window.tiKeepStatus = tiKeepStatus

function tiKeepStatus() {
    // 控制浏览器访问购物车详情页面, 以获取最新的有效Token
    if (TiAutoLoginIng) {
        return false
    }
    chrome.tabs.query({}, (tabs) => {
        let workTab = null
        for (let i = 0; i < tabs.length; i++) {
            if (tabs[i].url.indexOf('chrome-extension') === -1) {
                workTab = tabs[i]
                break
            }
        }
        if (workTab) {
            openTiCartPage(workTab.id)
        } else {
            chrome.tabs.create({active: false, url: `https://${tiOrigin}`}, (tab) => {
                // 设置定时任务监听tab的加载状态，记载完成后再进行下一步
                let tabStatusClock = setInterval(function () {
                    console.log("check tab status")
                    chrome.tabs.get(tab.id, function (tab) {
                        if (tab.status === "complete") {
                            clearInterval(tabStatusClock);
                            openTiCartPage(tab.id)
                        }
                    })
                }, 2000)
            })
        }
    })

}

function initBackground() {
    let tiLoginBtn = document.getElementById('tiLogin');
    tiLoginBtn.addEventListener('click', tiLogin)
    document.getElementById('email').value = localStorage.getItem("email")
    document.getElementById('password').value = localStorage.getItem("password")
}

window.onload = initBackground










