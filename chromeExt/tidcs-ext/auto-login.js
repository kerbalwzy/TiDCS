console.log("[Debug] Content-Script:tiAutoLogin loaded!");
const WaitEleTimes = 30
const WaitEleInterval = 1000
const myExtensionId = chrome.runtime.id;
let IsAutoLoginIng = false

// 等待某个元素加载完成, 再执行任务
function _waitEleDom(selector, times, interval) {
    // selector: JS选择器
    // times: 重试次数
    // interval: 重试间隔
    let _times = times || -1,
        _interval = interval || 500,
        _selector = selector,
        _iIntervalID // 定时器ID

    return new Promise(function (resolve, reject) {
        _iIntervalID = setInterval(function () {
            if (!_times) {
                clearInterval(_iIntervalID)
                reject('元素获取超时')
            }
            _times <= 0 || _times-- //如果是正数就 --
            let _eleDom = document.querySelector(_selector)
            if (_eleDom !== null) {
                clearInterval(_iIntervalID)
                resolve(_eleDom)
            }
        }, _interval)
    })
}

function waitEleDom(selector) {
    return _waitEleDom(selector, WaitEleTimes, WaitEleInterval)
}

function waitAnyEleDom(selectorArray, times, interval) {
    /**
     *@desc 等待任意个元素中的某个元素加载完成
     *@param {array} selectorArray JS选择器列表
     *@param {int} times 重试次数
     *@param {int} interval 重试时间间隔
     */
    let _times = times || -1,
        _interval = interval || 500,
        _iIntervalID // 定时器ID

    return new Promise(function (resolve, reject) {
        _iIntervalID = setInterval(function () {
            if (!_times) {
                clearInterval(_iIntervalID)
                reject('元素获取超时')
            }
            _times <= 0 || _times-- //如果是正数就 --
            for (let i = 0; i < selectorArray.length; i++) {
                let _selector = selectorArray[i]
                let _eleDom = document.querySelector(_selector)
                if (_eleDom !== null) {
                    clearInterval(_iIntervalID)
                    resolve(_eleDom)
                    return
                }
            }

        }, _interval)
    })
}

// 为元素分发Dom事件
function eleDomDispatchEvent(eleDom, eventName) {
    // eleDom: 元素DOM对象
    // eventName: 事件名称
    let _ev = document.createEvent('HTMLEvents')
    _ev.initEvent(eventName, true, true)
    eleDom.dispatchEvent(_ev)
    console.debug("Dispatch Event", eleDom, _ev)
}

// 睡眠，时间单位为毫秒
function sleep(time) {
    // time: 睡眠时间, 毫秒(ms)
    let startTime = new Date().getTime() + parseInt(time, 10);
    while (new Date().getTime() < startTime) {
    }
}

// 发送消息到background
function sendMsg2Background(msg, callback) {
    /*
    @params msg {object} 消息数据对象,要求可以被JSON序列化为字典
    @params callback {function} 回调函数，接受一个响应体数据作为参数
     */
    msg.recipient = "background"; // 添加接收者名称
    msg.action = "tiAutoLogin"; // 添加行为
    chrome.runtime.sendMessage(
        myExtensionId,
        msg,
        function (resp) {
            callback ? callback(resp) : null
        }
    )
}

// 自动登录任务
function autoLogin(email, password) {
    // 输入邮箱
    IsAutoLoginIng = true
    waitEleDom('#username-screen > div.u-margin-top-s > input').then((emailInput) => {
        emailInput.value = email
        eleDomDispatchEvent(emailInput, "input")
        // 点击下一步
        waitEleDom('#nextbutton').then((nextStepBtn) => {
            eleDomDispatchEvent(nextStepBtn, "click")
            // 输入密码
            waitEleDom('#password > input[type=password]').then((pwdInput) => {
                pwdInput.value = password
                eleDomDispatchEvent(emailInput, "input")
                // 点击登录
                waitEleDom('#loginbutton').then((loginBtn) => {
                    eleDomDispatchEvent(loginBtn, "click")
                    sendMsg2Background({msg: "登录成功"})
                }).catch(() => {
                    let err = "tiAutoLogin: 获取登录button元素失败"
                    console.log(err)
                    sendMsg2Background({errmsg: err})
                })
            }).catch(() => {
                let err = "tiAutoLogin: 获取密码input元素失败"
                console.log(err)
                sendMsg2Background({errmsg: err})

            })
        }).catch(() => {
            let err = "tiAutoLogin: 获取邮箱输入后下一步button元素失败"
            console.log(err)
            sendMsg2Background({errmsg: err})
        })
    }).catch(() => {
        let err = "tiAutoLogin: 获取邮箱input元素失败"
        console.log(err)
        sendMsg2Background({errmsg: err})
    })
}

/*
 * Notice: 'message.recipient' is self-defined
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (sender.id === myExtensionId && message.recipient === 'content') {
            let task = message.task;
            console.log(task)
            switch (task.cmd) {
                case "tiLogin":
                    autoLogin(task.email, task.password)
                    break
                default:
                    let err = "Unknow cmd: " + task.cmd + ", Content-Script can not handle"
                    console.debug(err)
                    sendMsg2Background({errmsg: err})
            }
        }
    }
);

function autoLoginBySelf() {
    console.log("autoLoginBySelf")
    let msg = {
        recipient: "background", // 添加接收者名称
        action: "tiAutoLoginBySelf"// 添加行为
    }
    chrome.runtime.sendMessage(
        myExtensionId,
        msg,
        function (resp) {
            if (resp.email && resp.password) {
                autoLogin(resp.email, resp.password)
            }
        }
    )
}

setTimeout(autoLoginBySelf, 5000)







