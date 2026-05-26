import { Component, OnInit } from '@angular/core';
import { PetService, Owner } from './PetService';

@Component({
  selector: 'app-owner-list',
  templateUrl: './owner-list.component.html',
})
export class OwnerListComponent implements OnInit {
  owners: Owner[] = [];
  searchName = '';

  constructor(private petService: PetService) {}

  ngOnInit(): void {
    this.loadOwners();
  }

  loadOwners(): void {
    this.petService.getOwners().subscribe(data => {
      this.owners = data;
    });
  }

  search(): void {
    this.petService.searchOwners(this.searchName).subscribe(data => {
      this.owners = data;
    });
  }
}
