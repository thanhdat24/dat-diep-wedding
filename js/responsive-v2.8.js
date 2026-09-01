(function(){
  "use strict";

  var DESIGN_WIDTH=420;
  var wrapper=null;
  var shell=null;
  var ro=null;
  var raf=0;

  function ensureShell(){
    wrapper=document.querySelector(".ladi-wraper");
    if(!wrapper)return false;

    if(wrapper.parentElement&&wrapper.parentElement.id==="wedding-responsive-shell"){
      shell=wrapper.parentElement;
      return true;
    }

    shell=document.createElement("div");
    shell.id="wedding-responsive-shell";
    wrapper.parentNode.insertBefore(shell,wrapper);
    shell.appendChild(wrapper);
    return true;
  }

  function fit(){
    if(!wrapper||!shell)return;

    var vw=document.documentElement.clientWidth||window.innerWidth||DESIGN_WIDTH;
    var scale=Math.min(1,vw/DESIGN_WIDTH);
    var rendered=DESIGN_WIDTH*scale;
    var left=Math.max(0,(vw-rendered)/2);

    wrapper.style.position="absolute";
    wrapper.style.top="0";
    wrapper.style.left=left+"px";
    wrapper.style.width=DESIGN_WIDTH+"px";
    wrapper.style.transformOrigin="top left";
    wrapper.style.transform="scale("+scale+")";

    var h=wrapper.scrollHeight||wrapper.offsetHeight||0;
    shell.style.height=Math.ceil(h*scale)+"px";
  }

  function requestFit(){
    cancelAnimationFrame(raf);
    raf=requestAnimationFrame(fit);
  }

  function start(){
    if(!ensureShell())return;
    fit();

    if("ResizeObserver" in window){
      ro=new ResizeObserver(requestFit);
      ro.observe(wrapper);
    }

    window.addEventListener("resize",requestFit,{passive:true});
    window.addEventListener("orientationchange",function(){
      setTimeout(requestFit,120);
    },{passive:true});

    setTimeout(requestFit,250);
    setTimeout(requestFit,900);
  }

  if(document.readyState==="loading"){
    document.addEventListener("DOMContentLoaded",start,{once:true});
  }else{
    start();
  }
})();