/**
* App Module
*
* Main App Module
*/
var app = angular.module('app', ['ngRoute']);

app.config(['$routeProvider','$locationProvider',
	function($routeProvider,$locationProvider) {
		$routeProvider
			.when('/',{
				controller:'mainController',
				title:"OpenBazaar"
			});

		// Use HTML5 History API
		$locationProvider.html5Mode(true);
}]);

app.controller('mainController', function(){});

app.controller('downloadController', function($scope,OSdetect) {

	var $linux = {
			ftype: 'application/x-gzip',
			download : 'file.gzip'
		},
		$apple = {
			ftype: 'application/x-gzip',
			download : 'file.gzip'
		},
		$win = {
			ftype: 'application/x-gzip',
			download : 'file.gzip'
		};
	$scope.currentos = "Alpha 1.2";
	$scope.currentos = OSdetect.name();
	$scope.download = {

		linux : function() {
			var blob = new Blob([$linux.download], { type: $linux.ftype });
			var downloadUrl = (window.URL || window.webkitURL).createObjectURL( blob );
			return downloadUrl;
		},
		apple : function() {
			var blob = new Blob([$apple.download], { type: $apple.ftype });
			var downloadUrl = (window.URL || window.webkitURL).createObjectURL( blob );
			return downloadUrl;
			},
		win : function() {
			var blob = new Blob([$win.download], { type: $win.ftype });
			var downloadUrl = (window.URL || window.webkitURL).createObjectURL( blob );
			return downloadUrl;
		}
	};
});

// OS Detector Factory
app.service('OSdetect', function(){
	this.name = function() {
		var OSname = "?";
		if (navigator.appVersion.indexOf("Win")!=-1) OSname="windows";
		if (navigator.appVersion.indexOf("Mac")!=-1) OSname="apple";
		if (navigator.appVersion.indexOf("X11")!=-1) OSname="windows";
		if (navigator.appVersion.indexOf("Linux")!=-1) OSname="linux";
		return OSname;
	};
});

//Directive + jQuery to collapse the navbar on scroll
app.directive('navbarScroll', function(){
	return {
		restrict: 'C',
		link: function($scope,element) {
			$(window).scroll(function() {
				if ($(element).offset().top > 50) {
					$(element).addClass("navbar-collapse");
				} else {
					$(element).removeClass("navbar-collapse");
				}
			});
		}
	};
});

//Directive + jQuery Set Front Jumbotron Height to Window
app.directive('windowHeight', function(){
	return {
		restrict: 'C',
		link: function($scope,element) {
			// Toggle Resize Function on Resizing
			$(window).resize(function() {
				var height = $(window).height();
				height = height-290;
				$(element).height(height);
			}).resize();
		}
	};
});


