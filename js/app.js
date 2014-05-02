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
				templateUrl:'partials/home.html',
				controller:'mainController',
				title:"OpenBazaar"
			});

		// Use HTML5 History API
		$locationProvider.html5Mode(true);
}]);

app.controller('mainController',function($scope) {
	$scope.page = {
		title: "OpenBazaar"
	};
	$scope.url = {
		url1: "Hello"
	};
	$scope.Osfind = OSdetect;
});

// OS Detector Factory
function OSdetect() {
	this.name = function() {
		var OSname = "Unknown OS";
		if (navigator.appVersion.indexOf("Win")!=-1) OSName="Windows";
		if (navigator.appVersion.indexOf("Mac")!=-1) OSName="MacOS";
		if (navigator.appVersion.indexOf("X11")!=-1) OSName="UNIX";
		if (navigator.appVersion.indexOf("Linux")!=-1) OSName="Linux";
		return OSname;
	};
}

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


