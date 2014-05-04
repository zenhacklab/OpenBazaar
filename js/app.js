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

	$scope.currentos = OSdetect.name();
	$scope.appversion = "Alpha 1.2";

	$scope.linux = function() {
		var ftype = 'application/x-gzip',
			download = 'file.gzip',
			blob = new Blob([$linux.download], { type: $linux.ftype }),
			downloadUrl = (window.URL || window.webkitURL).createObjectURL( blob );
		return { url: downloadUrl, download: download };
	};

	$scope.apple = function() {
		var ftype = 'application/x-gzip',
			download = 'file.gzip',
			blob = new Blob([$apple.download], { type: $apple.ftype }),
			downloadUrl = (window.URL || window.webkitURL).createObjectURL( blob );
		return { url: downloadUrl, download: download };
	};
	$scope.windows = function() {
		var ftype = 'application/x-gzip',
			download = 'file.gzip',
			blob = new Blob([$win.download], { type: $win.ftype }),
			downloadUrl = (window.URL || window.webkitURL).createObjectURL( blob );
		return { url: downloadUrl, download: download };
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

//Directive + jQuery Detect and Hide Other OS Download Links
app.directive('osHighlight', function(){
	return {
		restrict: 'AC',
		controller: 'downloadController',
		link: function($scope,element,attrs) {
			// Check and Hide other OS but Current One
			attrs.$observe('osHighlight', function(value) {
				if (value == $scope.currentos) {
					element.addClass('highlight');
				}
			});
		}
	};
});

//Directive + jQuery Add Top Download Link with Responsive os link.
app.directive('downloadTop', function(){
	return {
		restrict: 'A',
		controller: 'downloadController',
		link: function($scope,element,attrs) {
			// Check and Hide other OS but Current One
			var os = $scope.currentos;

			if (os == "windows"){fn = $scope.windows();}
			if (os == "apple"){fn = $scope.apple();}
			if (os == "linux"){fn = $scope.linux();}

			attrs.$set('download', fn.download);
			attrs.$set('ngHref', fn.url);
		}
	};
});




